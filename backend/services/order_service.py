import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.models import Food, Order, OrderStatus, PlatformBalance, User
from backend.models.enums import ORDER_TRANSITIONS, PaymentMethod, PaymentStatus
from backend.services import notification_service, referral_service
from backend.utils.ton import is_valid_ton_address

logger = logging.getLogger(__name__)

DUPLICATE_WINDOW = timedelta(minutes=2)


class OrderError(Exception):
    pass


def _order_query():
    return select(Order).options(
        selectinload(Order.food),
        selectinload(Order.buyer),
        selectinload(Order.cook),
    )


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(_order_query().where(Order.id == order_id))
    return result.scalar_one_or_none()


async def create_order(
    session: AsyncSession,
    buyer: User,
    food_id: int,
    quantity: int,
    comment: str = "",
    payment_method: str = PaymentMethod.STARS.value,
) -> Order:
    if quantity < 1:
        raise OrderError("Количество должно быть не меньше 1")

    food = await session.get(Food, food_id, options=[selectinload(Food.cook)])
    if food is None or not food.is_active:
        raise OrderError("Блюдо недоступно")
    if food.cook_id == buyer.id:
        raise OrderError("Нельзя заказать собственное блюдо")
    if food.portions < quantity:
        raise OrderError(f"Доступно только {food.portions} порций")

    # Duplicate protection: identical active order within a short window.
    since = datetime.now(timezone.utc) - DUPLICATE_WINDOW
    dup_result = await session.execute(
        select(Order.id).where(
            Order.buyer_id == buyer.id,
            Order.food_id == food_id,
            Order.status == OrderStatus.NEW.value,
            Order.created_at >= since,
        )
    )
    if dup_result.first() is not None:
        raise OrderError("Похожий заказ уже оформлен. Дождитесь ответа повара.")

    if payment_method not in {m.value for m in PaymentMethod}:
        raise OrderError("Неизвестный способ оплаты")
    if payment_method == PaymentMethod.TON.value:
        wallet = (food.cook.ton_wallet_address or "").strip()
        if not is_valid_ton_address(wallet):
            raise OrderError("Повар ещё не подключил TON-кошелёк для приёма оплаты")

    gross = round(food.price * quantity, 2)
    referral_discount = referral_service.apply_referral_discount(buyer, gross)
    total_price = round(gross - referral_discount, 2)

    order = Order(
        buyer_id=buyer.id,
        cook_id=food.cook_id,
        food_id=food.id,
        quantity=quantity,
        total_price=total_price,
        status=OrderStatus.NEW.value,
        comment=comment.strip()[:512],
        payment_method=payment_method,
        payment_status=PaymentStatus.PENDING.value,
        referral_discount=referral_discount,
    )
    food.portions -= quantity
    session.add(order)
    await session.commit()

    order = await get_order(session, order.id)
    logger.info("Order #%s created: buyer=%s food=%s qty=%s", order.id, buyer.id, food.id, quantity)
    return order


async def confirm_ton_payment(session: AsyncSession, order_id: int, buyer: User) -> Order:
    order = await get_order(session, order_id)
    if order is None:
        raise OrderError("Заказ не найден")
    if order.buyer_id != buyer.id:
        raise OrderError("Нет доступа к этому заказу")
    if order.payment_method != PaymentMethod.TON.value:
        raise OrderError("Заказ не оплачивается TON")
    if order.status == OrderStatus.CANCELLED.value:
        raise OrderError("Заказ отменён")
    if order.payment_status == PaymentStatus.PAID.value:
        return order

    order.payment_status = PaymentStatus.PAID.value
    await session.commit()
    order = await get_order(session, order_id)
    await notification_service.notify_cook_new_order(order, order.food, order.cook, order.buyer)
    await notification_service.notify_buyer_ton_paid(order, order.food, order.buyer)
    logger.info("Order #%s marked paid via TON", order.id)
    return order


async def change_status(
    session: AsyncSession,
    order_id: int,
    new_status: OrderStatus,
    actor: User,
) -> Order:
    order = await get_order(session, order_id)
    if order is None:
        raise OrderError("Заказ не найден")

    is_cook = actor.id == order.cook_id
    is_buyer = actor.id == order.buyer_id
    if not is_cook and not is_buyer:
        raise OrderError("Нет доступа к этому заказу")

    current = OrderStatus(order.status)
    if new_status not in ORDER_TRANSITIONS[current]:
        raise OrderError(f"Нельзя перевести заказ из «{current.value}» в «{new_status.value}»")

    # Buyers may only cancel their own NEW orders; everything else is cook-only.
    if is_buyer and not is_cook:
        if not (new_status == OrderStatus.CANCELLED and current == OrderStatus.NEW):
            raise OrderError("Покупатель может только отменить новый заказ")

    order.status = new_status.value

    if new_status == OrderStatus.CANCELLED:
        food = await session.get(Food, order.food_id)
        if food is not None:
            food.portions += order.quantity
        if order.referral_discount > 0:
            await referral_service.restore_referral_discount(
                session, order.buyer, order.referral_discount
            )

    referral_notify = None
    if new_status == OrderStatus.DELIVERED:
        food = await session.get(Food, order.food_id)
        if food is not None:
            food.orders_count += 1
        if order.payment_status != PaymentStatus.PAID.value:
            order.payment_status = PaymentStatus.PAID.value
        await _accrue_platform_commission(session, order)
        referral_notify = await referral_service.on_order_delivered(session, order)

    await session.commit()
    order = await get_order(session, order_id)

    if referral_notify is not None:
        buyer_n, referrer_n, ref_bonus, inv_bonus = referral_notify
        await notification_service.notify_referral_rewards(buyer_n, referrer_n, ref_bonus, inv_bonus)

    await notification_service.notify_buyer_status(order, order.food, order.buyer)
    if is_buyer and not is_cook:
        await notification_service.notify_cook_status(order, order.food, order.cook)

    logger.info("Order #%s -> %s (by user %s)", order.id, new_status.value, actor.id)
    return order


async def _accrue_platform_commission(session: AsyncSession, order: Order) -> None:
    """Accrue 1% platform commission exactly once per delivered order."""
    existing = await session.execute(
        select(PlatformBalance.id).where(PlatformBalance.order_id == order.id)
    )
    if existing.first() is not None:
        return
    amount = round(order.total_price * settings.platform_commission_rate, 2)
    session.add(PlatformBalance(order_id=order.id, amount=amount))
    logger.info("Platform commission %.2f accrued for order #%s", amount, order.id)


async def get_buyer_orders(session: AsyncSession, buyer: User) -> list[Order]:
    result = await session.execute(
        _order_query().where(Order.buyer_id == buyer.id).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def get_cook_orders(session: AsyncSession, cook: User) -> list[Order]:
    result = await session.execute(
        _order_query().where(Order.cook_id == cook.id).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())
