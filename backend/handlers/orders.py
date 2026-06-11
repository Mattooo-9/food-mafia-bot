import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from backend.database import async_session_factory
from backend.models import OrderStatus
from backend.services import user_service
from backend.services.notification_service import STATUS_LABELS, cook_order_keyboard
from backend.services.order_service import OrderError, change_status, get_order

logger = logging.getLogger(__name__)

router = Router(name="orders")


@router.callback_query(F.data.startswith("order:"))
async def order_status_callback(callback: CallbackQuery) -> None:
    try:
        _, order_id_raw, status_raw = callback.data.split(":")
        order_id = int(order_id_raw)
        new_status = OrderStatus(status_raw)
    except (ValueError, KeyError):
        await callback.answer("Некорректные данные", show_alert=True)
        return

    async with async_session_factory() as session:
        actor = await user_service.get_user_by_tg_id(session, callback.from_user.id)
        if actor is None:
            await callback.answer("Сначала отправьте /start боту", show_alert=True)
            return
        try:
            order = await change_status(session, order_id, new_status, actor)
        except OrderError as exc:
            await callback.answer(str(exc), show_alert=True)
            # Refresh keyboard to reflect actual current status.
            current = await get_order(session, order_id)
            if current is not None and callback.message is not None:
                try:
                    await callback.message.edit_reply_markup(
                        reply_markup=cook_order_keyboard(current)
                    )
                except TelegramAPIError:
                    pass
            return

    label = STATUS_LABELS.get(order.status, order.status)
    await callback.answer(f"Статус: {label}")
    if callback.message is not None:
        try:
            await callback.message.edit_text(
                f"Заказ #{order.id}\n"
                f"🍽 {order.food.name} × {order.quantity}\n"
                f"💰 {order.total_price:.2f} ₽\n"
                f"Статус: {label}",
                reply_markup=cook_order_keyboard(order),
            )
        except TelegramAPIError as exc:
            logger.warning("Failed to edit order message: %s", exc)
