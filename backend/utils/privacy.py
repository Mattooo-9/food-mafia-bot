"""Анонимизация: чужие имена и координаты не утекают в API."""

from __future__ import annotations

from backend.models import User


def anonymize_user(user: User) -> str:
    """Стабильный псевдоним без username и tg_id."""
    code = (user.id * 2_654_435_761) % 9000 + 1000
    return f"Гость ·{code:04d}"


def buyer_display(buyer: User, viewer: User | None) -> str:
    if viewer and viewer.id == buyer.id:
        return "Вы"
    return anonymize_user(buyer)


def cook_display(cook: User, viewer: User | None) -> str:
    if viewer and viewer.id == cook.id:
        return "Вы"
    return cook.cook_name or cook.first_name or "Повар"


def geo_label(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "Гео выкл"
    return "Рядом с вами"
