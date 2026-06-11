from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    COOKING = "COOKING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Allowed transitions: who can move an order from one status to another.
ORDER_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.NEW: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
    OrderStatus.ACCEPTED: [OrderStatus.COOKING, OrderStatus.CANCELLED],
    OrderStatus.COOKING: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}

FOOD_CATEGORIES: list[str] = [
    "Горячее",
    "Супы",
    "Салаты",
    "Выпечка",
    "Десерты",
    "Завтраки",
    "Напитки",
    "Закуски",
    "Другое",
]
