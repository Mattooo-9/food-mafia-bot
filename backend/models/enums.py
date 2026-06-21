from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    COOKING = "COOKING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    STARS = "STARS"
    TON = "TON"


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"


PAYMENT_METHOD_LABELS: dict[str, str] = {
    PaymentMethod.STARS.value: "Telegram Stars",
    PaymentMethod.TON.value: "TON",
    # Legacy
    "CASH": "Наличные",
    "TRANSFER": "Перевод",
    "CARD": "Картой",
}

PAYMENT_STATUS_LABELS: dict[str, str] = {
    PaymentStatus.PENDING.value: "Ожидает оплаты",
    PaymentStatus.PAID.value: "Оплачено",
}


# Allowed transitions: who can move an order from one status to another.
ORDER_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.NEW: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
    OrderStatus.ACCEPTED: [OrderStatus.COOKING, OrderStatus.CANCELLED],
    OrderStatus.COOKING: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}

FOOD_CATEGORIES: list[str] = sorted(
    [
        "Выпечка",
        "Горячее",
        "Десерты",
        "Завтраки",
        "Закуски",
        "Напитки",
        "Салаты",
        "Супы",
        "Другое",
    ],
    key=lambda c: (c == "Другое", c),
)
