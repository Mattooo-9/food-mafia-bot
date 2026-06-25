"""Краткие подсказки для главного экрана — без лишних запросов с фронта."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Order, OrderWish, OrderWishStatus, User
from backend.models.enums import OrderStatus
from backend.services import memory_service, nutrition_service
from backend.utils.privacy import geo_label


async def user_insights(session: AsyncSession, user: User) -> dict:
    active_orders = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Order)
                .where(Order.buyer_id == user.id)
                .where(Order.status.not_in((OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value)))
            )
        ).scalar_one()
    )

    open_wishes = int(
        (
            await session.execute(
                select(func.count())
                .select_from(OrderWish)
                .where(OrderWish.buyer_id == user.id)
                .where(OrderWish.status == OrderWishStatus.OPEN.value)
            )
        ).scalar_one()
    )

    claimed_wishes = int(
        (
            await session.execute(
                select(func.count())
                .select_from(OrderWish)
                .where(OrderWish.buyer_id == user.id)
                .where(OrderWish.status == OrderWishStatus.CLAIMED.value)
            )
        ).scalar_one()
    )

    companion = await memory_service.companion_line(session, user)
    tip = await nutrition_service.wellness_tip(session, user)

    lines: list[str] = []
    if companion:
        lines.append(companion)
    meal = tip.get("message", "")
    if meal and meal not in lines:
        lines.append(meal)

    return {
        "has_location": user.lat is not None and user.lon is not None,
        "geo_label": geo_label(user.lat, user.lon),
        "meal_hint": meal,
        "memory_hint": companion,
        "summary": " · ".join(lines)[:200] if lines else meal[:120],
        "active_orders": active_orders,
        "open_wishes": open_wishes,
        "claimed_wishes": claimed_wishes,
    }
