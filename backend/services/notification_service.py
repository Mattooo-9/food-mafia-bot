import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.bot_instance import bot
from backend.models import Food, Order, OrderStatus, Subscription, User
from backend.models.enums import PAYMENT_METHOD_LABELS
from backend.utils.privacy import anonymize_user, buyer_display

logger = logging.getLogger(__name__)

STATUS_LABELS: dict[str, str] = {
    OrderStatus.NEW.value: "🆕 Новый",
    OrderStatus.ACCEPTED.value: "✅ Принят",
    OrderStatus.COOKING.value: "🍳 Готовится",
    OrderStatus.READY.value: "🍱 Готов к выдаче",
    OrderStatus.DELIVERED.value: "📦 Доставлен",
    OrderStatus.CANCELLED.value: "❌ Отменён",
}


async def _send(tg_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    try:
        await bot.send_message(tg_id, text, reply_markup=reply_markup)
    except TelegramAPIError as exc:
        logger.warning("Failed to send notification to %s: %s", tg_id, exc)


def cook_order_keyboard(order: Order) -> InlineKeyboardMarkup:
    status = order.status
    rows: list[list[InlineKeyboardButton]] = []
    if status == OrderStatus.NEW.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"order:{order.id}:{OrderStatus.ACCEPTED.value}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"order:{order.id}:{OrderStatus.CANCELLED.value}",
                ),
            ]
        )
    elif status == OrderStatus.ACCEPTED.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🍳 Готовлю", callback_data=f"order:{order.id}:{OrderStatus.COOKING.value}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"order:{order.id}:{OrderStatus.CANCELLED.value}",
                ),
            ]
        )
    elif status == OrderStatus.COOKING.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🍱 Готово", callback_data=f"order:{order.id}:{OrderStatus.READY.value}"
                )
            ]
        )
    elif status == OrderStatus.READY.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📦 Выдан", callback_data=f"order:{order.id}:{OrderStatus.DELIVERED.value}"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _stars(amount: float) -> str:
    return f"{amount:.0f} ⭐"


def _order_summary(order: Order, food: Food) -> str:
    pay = PAYMENT_METHOD_LABELS.get(order.payment_method, order.payment_method)
    lines = [
        f"Заказ #{order.id}",
        f"🍽 {food.name} × {order.quantity}",
        f"💰 {_stars(order.total_price)}",
        f"💳 {pay}",
    ]
    if order.referral_discount > 0:
        lines.append(f"🎁 Скидка с баланса: −{_stars(order.referral_discount)}")
    if order.comment:
        lines.append(f"💬 {order.comment}")
    return "\n".join(lines)


async def notify_cook_new_order(order: Order, food: Food, cook: User, buyer: User) -> None:
    buyer_name = buyer_display(buyer, None)
    text = (
        f"🔔 <b>Новый заказ!</b>\n\n{_order_summary(order, food)}\n"
        f"👤 Покупатель: {buyer_name}"
    )
    await _send(cook.tg_id, text, reply_markup=cook_order_keyboard(order))


async def notify_buyer_status(order: Order, food: Food, buyer: User) -> None:
    label = STATUS_LABELS.get(order.status, order.status)
    headers = {
        OrderStatus.ACCEPTED.value: "Повар принял ваш заказ!",
        OrderStatus.COOKING.value: "Повар начал готовить ваш заказ.",
        OrderStatus.READY.value: "Ваш заказ готов к выдаче! 🎉",
        OrderStatus.DELIVERED.value: "Заказ завершён. Спасибо! Оцените повара в приложении.",
        OrderStatus.CANCELLED.value: "Заказ отменён.",
    }
    header = headers.get(order.status, "Статус заказа изменён.")
    text = f"<b>{header}</b>\n\n{_order_summary(order, food)}\nСтатус: {label}"
    await _send(buyer.tg_id, text)


async def notify_cook_status(order: Order, food: Food, cook: User) -> None:
    label = STATUS_LABELS.get(order.status, order.status)
    text = f"Заказ #{order.id} — статус: {label}\n🍽 {food.name} × {order.quantity}"
    await _send(cook.tg_id, text, reply_markup=cook_order_keyboard(order))


async def notify_buyer_stars_paid(order: Order, food: Food, buyer: User) -> None:
    text = (
        f"✅ <b>Оплата прошла!</b>\n\n{_order_summary(order, food)}\n"
        "Повар получил заказ и скоро ответит."
    )
    await _send(buyer.tg_id, text)


async def notify_buyer_ton_paid(order: Order, food: Food, buyer: User) -> None:
    text = (
        f"✅ <b>TON отправлен!</b>\n\n{_order_summary(order, food)}\n"
        "Повар получил заказ и скоро ответит."
    )
    await _send(buyer.tg_id, text)


async def notify_referral_rewards(
    buyer: User, referrer: User | None, referee_bonus: float, referrer_bonus: float
) -> None:
    await _send(
        buyer.tg_id,
        f"🎁 <b>+{_stars(referee_bonus)}</b> на баланс за первый заказ!\n"
        "Используйте при следующем заказе в приложении.",
    )
    if referrer is None:
        return
    name = anonymize_user(buyer)
    await _send(
        referrer.tg_id,
        f"🎁 <b>+{_stars(referrer_bonus)}</b> на ваш баланс!\n"
        f"{name} оформил первый заказ по вашей ссылке.",
    )


async def notify_subscribers_new_food(session: AsyncSession, food: Food, cook: User) -> None:
    result = await session.execute(
        select(User.tg_id)
        .join(Subscription, Subscription.user_id == User.id)
        .where(Subscription.cook_id == cook.id)
    )
    tg_ids = [row[0] for row in result.all()]
    if not tg_ids:
        return
    cook_name = cook.cook_name or cook.first_name or "Повар"
    text = (
        f"🍽 <b>{cook_name}</b> добавил новое блюдо!\n\n"
        f"<b>{food.name}</b> — {_stars(food.price)}\n{food.description}"
    )
    for tg_id in tg_ids:
        await _send(tg_id, text)


async def notify_cooks_new_wish(session: AsyncSession, wish) -> None:
    result = await session.execute(
        select(User).where(User.is_cook.is_(True), User.is_online.is_(True))
    )
    cooks = list(result.scalars().all())
    buyer = wish.buyer
    buyer_name = buyer_display(buyer, None)
    budget = f"до {_stars(wish.budget_max)}" if wish.budget_max else "по договорённости"
    text = (
        f"📋 <b>Новый запрос от покупателя!</b>\n\n"
        f"«{wish.title}» × {wish.portions}\n"
        f"💰 {budget}\n"
        f"👤 {buyer_name}"
    )
    if wish.details:
        text += f"\n💬 {wish.details[:200]}"
    text += "\n\nОткройте «Моя кухня» → «Запросы» чтобы взять заказ."
    for cook in cooks:
        if cook.id == wish.buyer_id:
            continue
        await _send(cook.tg_id, text)


async def notify_buyer_wish_claimed(wish) -> None:
    cook = wish.cook
    if cook is None or wish.buyer is None:
        return
    cook_name = cook.cook_name or cook.first_name or "Повар"
    await _send(
        wish.buyer.tg_id,
        f"✅ <b>{cook_name}</b> взял ваш запрос «{wish.title}».\n"
        "Свяжитесь в чате Telegram или уточните детали в приложении.",
    )
