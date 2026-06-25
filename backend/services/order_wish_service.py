"""Маркетплейс заказов: покупатель публикует запрос, повар забирает."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import OrderWish, OrderWishStatus, User
from backend.services import notification_service
from backend.utils.categories import categorize_text
from backend.utils.geo import haversine_m

logger = logging.getLogger(__name__)


class OrderWishError(Exception):
    pass


def _query():
    return select(OrderWish).options(
        selectinload(OrderWish.buyer),
        selectinload(OrderWish.cook),
    )


async def create_wish(
    session: AsyncSession,
    buyer: User,
    title: str,
    details: str = "",
    budget_max: float | None = None,
    portions: int = 1,
) -> OrderWish:
    title = title.strip()
    if len(title) < 2:
        raise OrderWishError("Опишите заказ короче: минимум 2 символа")
    if portions < 1:
        raise OrderWishError("Укажите количество порций")

    cat = categorize_text(query=title + " " + details)
    wish = OrderWish(
        buyer_id=buyer.id,
        title=title[:128],
        details=details.strip()[:2000],
        category_path=cat["path"] if cat["group"] != "Разное" else None,
        budget_max=round(budget_max, 2) if budget_max and budget_max > 0 else None,
        portions=portions,
        status=OrderWishStatus.OPEN.value,
    )
    session.add(wish)
    await session.commit()
    wish = await get_wish(session, wish.id)
    from backend.services import memory_service

    await memory_service.observe_search(
        session,
        buyer,
        title,
        category_hint=cat,
        results_count=0,
        price_max=budget_max,
    )
    await session.commit()
    await notification_service.notify_cooks_new_wish(session, wish)
    logger.info("OrderWish #%s created by user %s", wish.id, buyer.id)
    return wish


async def get_wish(session: AsyncSession, wish_id: int) -> OrderWish | None:
    result = await session.execute(_query().where(OrderWish.id == wish_id))
    return result.scalar_one_or_none()


async def list_buyer_wishes(session: AsyncSession, buyer: User) -> list[OrderWish]:
    result = await session.execute(
        _query().where(OrderWish.buyer_id == buyer.id).order_by(OrderWish.created_at.desc())
    )
    return list(result.scalars().all())


async def list_cook_claimed_wishes(session: AsyncSession, cook: User) -> list[OrderWish]:
    result = await session.execute(
        _query()
        .where(OrderWish.cook_id == cook.id)
        .where(OrderWish.status == OrderWishStatus.CLAIMED.value)
        .order_by(OrderWish.claimed_at.desc())
    )
    return list(result.scalars().all())


async def list_open_wishes(
    session: AsyncSession,
    cook: User,
    *,
    max_distance_m: float | None = 15000,
) -> list[tuple[OrderWish, float | None]]:
    result = await session.execute(
        _query()
        .where(OrderWish.status == OrderWishStatus.OPEN.value)
        .where(OrderWish.buyer_id != cook.id)
        .order_by(OrderWish.created_at.desc())
    )
    wishes = list(result.scalars().all())
    has_loc = cook.lat is not None and cook.lon is not None
    out: list[tuple[OrderWish, float | None]] = []
    for w in wishes:
        dist: float | None = None
        buyer = w.buyer
        if has_loc and buyer.lat is not None and buyer.lon is not None:
            dist = haversine_m(cook.lat, cook.lon, buyer.lat, buyer.lon)
        if max_distance_m is not None and dist is not None and dist > max_distance_m:
            continue
        out.append((w, dist))
    out.sort(key=lambda x: x[1] if x[1] is not None else float("inf"))
    return out


async def claim_wish(session: AsyncSession, cook: User, wish_id: int) -> OrderWish:
    if not cook.is_cook:
        raise OrderWishError("Только повара могут брать заказы")
    wish = await get_wish(session, wish_id)
    if wish is None:
        raise OrderWishError("Запрос не найден")
    if wish.status != OrderWishStatus.OPEN.value:
        raise OrderWishError("Заказ уже занят или закрыт")
    if wish.buyer_id == cook.id:
        raise OrderWishError("Нельзя взять свой запрос")

    wish.status = OrderWishStatus.CLAIMED.value
    wish.cook_id = cook.id
    wish.claimed_at = datetime.now(timezone.utc)
    await session.commit()
    wish = await get_wish(session, wish_id)
    await notification_service.notify_buyer_wish_claimed(wish)
    logger.info("OrderWish #%s claimed by cook %s", wish.id, cook.id)
    return wish


async def cancel_wish(session: AsyncSession, user: User, wish_id: int) -> OrderWish:
    wish = await get_wish(session, wish_id)
    if wish is None:
        raise OrderWishError("Запрос не найден")
    is_buyer = wish.buyer_id == user.id
    is_cook = wish.cook_id == user.id
    if not is_buyer and not is_cook:
        raise OrderWishError("Нет доступа")
    if wish.status in (OrderWishStatus.COMPLETED.value, OrderWishStatus.CANCELLED.value):
        raise OrderWishError("Заказ уже завершён")

    wish.status = OrderWishStatus.CANCELLED.value
    await session.commit()
    return await get_wish(session, wish_id)


async def complete_wish(session: AsyncSession, cook: User, wish_id: int) -> OrderWish:
    wish = await get_wish(session, wish_id)
    if wish is None or wish.cook_id != cook.id:
        raise OrderWishError("Заказ не найден")
    if wish.status != OrderWishStatus.CLAIMED.value:
        raise OrderWishError("Сначала примите заказ")

    wish.status = OrderWishStatus.COMPLETED.value
    await session.commit()
    return await get_wish(session, wish_id)
