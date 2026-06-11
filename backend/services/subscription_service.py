from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Subscription, User


async def subscribe(session: AsyncSession, user: User, cook_id: int) -> bool:
    cook = await session.get(User, cook_id)
    if cook is None or not cook.is_cook or cook.id == user.id:
        return False
    existing = await session.execute(
        select(Subscription.id).where(
            Subscription.user_id == user.id, Subscription.cook_id == cook_id
        )
    )
    if existing.first() is None:
        session.add(Subscription(user_id=user.id, cook_id=cook_id))
        await session.commit()
    return True


async def unsubscribe(session: AsyncSession, user: User, cook_id: int) -> None:
    await session.execute(
        delete(Subscription).where(
            Subscription.user_id == user.id, Subscription.cook_id == cook_id
        )
    )
    await session.commit()


async def get_subscriptions(session: AsyncSession, user: User) -> list[User]:
    result = await session.execute(
        select(User)
        .join(Subscription, Subscription.cook_id == User.id)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
    )
    return list(result.scalars().all())


async def get_subscription_cook_ids(session: AsyncSession, user: User) -> set[int]:
    result = await session.execute(
        select(Subscription.cook_id).where(Subscription.user_id == user.id)
    )
    return {row[0] for row in result.all()}
