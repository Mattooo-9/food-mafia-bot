from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    COOKING = "COOKING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    CARD = "CARD"
    CASH = "CASH"
    TRANSFER = "TRANSFER"


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"


PAYMENT_METHOD_LABELS: dict[str, str] = {
    PaymentMethod.CASH.value: "Наличные",
    PaymentMethod.TRANSFER.value: "Перевод",
    PaymentMethod.CARD.value: "Картой при получении",
}

PAYMENT_STATUS_LABELS: dict[str, str] = {
    PaymentStatus.PENDING.value: "Ожидает оплаты",
    PaymentStatus.PAID.value: "Оплачен",
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
