from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Order, OrderStatus, Review, User


class ReviewError(Exception):
    pass


async def create_review(
    session: AsyncSession,
    buyer: User,
    order_id: int,
    rating: int,
    text: str = "",
) -> Review:
    if not 1 <= rating <= 5:
        raise ReviewError("Оценка должна быть от 1 до 5")

    order = await session.get(Order, order_id)
    if order is None or order.buyer_id != buyer.id:
        raise ReviewError("Заказ не найден")
    if order.status != OrderStatus.DELIVERED.value:
        raise ReviewError("Оценить можно только завершённый заказ")

    existing = await session.execute(select(Review.id).where(Review.order_id == order_id))
    if existing.first() is not None:
        raise ReviewError("Отзыв на этот заказ уже оставлен")

    review = Review(
        order_id=order_id,
        buyer_id=buyer.id,
        cook_id=order.cook_id,
        rating=rating,
        text=text.strip()[:1000],
    )
    session.add(review)
    await session.flush()
    await _recalculate_cook_rating(session, order.cook_id)
    await session.commit()
    await session.refresh(review)
    return review


async def _recalculate_cook_rating(session: AsyncSession, cook_id: int) -> None:
    result = await session.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.cook_id == cook_id)
    )
    avg, count = result.one()
    cook = await session.get(User, cook_id)
    if cook is not None:
        cook.rating_avg = round(float(avg or 0.0), 2)
        cook.rating_count = int(count or 0)


async def get_cook_reviews(session: AsyncSession, cook_id: int, limit: int = 50) -> list[Review]:
    result = await session.execute(
        select(Review)
        .options(selectinload(Review.buyer))
        .where(Review.cook_id == cook_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_order_review(session: AsyncSession, order_id: int) -> Review | None:
    result = await session.execute(select(Review).where(Review.order_id == order_id))
    return result.scalar_one_or_none()
