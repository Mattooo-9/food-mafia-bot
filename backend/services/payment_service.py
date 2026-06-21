import logging

from aiogram.types import LabeledPrice

from backend.bot_instance import bot
from backend.config import settings
from backend.models import Food, Order, OrderStatus, PaymentMethod, PaymentStatus, User
from backend.utils.ton import is_valid_ton_address

logger = logging.getLogger(__name__)


def stars_amount(total: float) -> int:
    return max(1, int(round(total)))


def ton_amount(total_stars: float) -> float:
    return round(total_stars * settings.ton_per_star, 6)


def build_ton_payment(order: Order, cook: User) -> dict | None:
    wallet = (cook.ton_wallet_address or "").strip()
    if not wallet or not is_valid_ton_address(wallet):
        return None
    return {
        "wallet_address": wallet,
        "amount_ton": ton_amount(order.total_price),
        "comment": f"order-{order.id}",
    }


async def create_stars_invoice(order: Order, food: Food) -> str:
    amount = stars_amount(order.total_price)
    link = await bot.create_invoice_link(
        title=f"{food.name} × {order.quantity}",
        description=f"Заказ #{order.id} · Еда Рядом",
        payload=f"order:{order.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=food.name, amount=amount)],
    )
    logger.info("Stars invoice for order #%s: %s stars", order.id, amount)
    return link


def validate_stars_payment(order: Order, stars_paid: int) -> str | None:
    if order.payment_method != PaymentMethod.STARS.value:
        return "Заказ не оплачивается Stars"
    if order.payment_status == PaymentStatus.PAID.value:
        return "Заказ уже оплачен"
    if order.status == OrderStatus.CANCELLED.value:
        return "Заказ отменён"
    expected = stars_amount(order.total_price)
    if stars_paid != expected:
        return f"Неверная сумма: ожидалось {expected} ⭐"
    return None
