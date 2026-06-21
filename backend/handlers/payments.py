import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from backend.database import async_session_factory
from backend.models import PaymentStatus
from backend.services import notification_service, order_service, payment_service

logger = logging.getLogger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    payload = query.invoice_payload or ""
    if not payload.startswith("order:"):
        await query.answer(ok=False, error_message="Неизвестный заказ")
        return

    try:
        order_id = int(payload.split(":", 1)[1])
    except ValueError:
        await query.answer(ok=False, error_message="Неверный номер заказа")
        return

    async with async_session_factory() as session:
        order = await order_service.get_order(session, order_id)
        if order is None:
            await query.answer(ok=False, error_message="Заказ не найден")
            return
        if order.buyer.tg_id != query.from_user.id:
            await query.answer(ok=False, error_message="Это не ваш заказ")
            return
        err = payment_service.validate_stars_payment(order, query.total_amount)
        if err:
            await query.answer(ok=False, error_message=err)
            return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    sp = message.successful_payment
    if sp is None or sp.currency != "XTR":
        return

    payload = sp.invoice_payload or ""
    if not payload.startswith("order:"):
        return

    try:
        order_id = int(payload.split(":", 1)[1])
    except ValueError:
        return

    async with async_session_factory() as session:
        order = await order_service.get_order(session, order_id)
        if order is None:
            return
        err = payment_service.validate_stars_payment(order, sp.total_amount)
        if err:
            logger.warning("Stars payment rejected for order #%s: %s", order_id, err)
            return

        order.payment_status = PaymentStatus.PAID.value
        await session.commit()
        order = await order_service.get_order(session, order_id)

        await notification_service.notify_cook_new_order(
            order, order.food, order.cook, order.buyer
        )
        await notification_service.notify_buyer_stars_paid(order, order.food, order.buyer)

    logger.info("Order #%s paid with %s Stars", order_id, sp.total_amount)
