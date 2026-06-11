from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import FavoriteCook, FavoriteFood, Food, User


async def add_favorite_food(session: AsyncSession, user: User, food_id: int) -> bool:
    food = await session.get(Food, food_id)
    if food is None:
        return False
    existing = await session.execute(
        select(FavoriteFood.id).where(
            FavoriteFood.user_id == user.id, FavoriteFood.food_id == food_id
        )
    )
    if existing.first() is None:
        session.add(FavoriteFood(user_id=user.id, food_id=food_id))
        await session.commit()
    return True


async def remove_favorite_food(session: AsyncSession, user: User, food_id: int) -> None:
    await session.execute(
        delete(FavoriteFood).where(
            FavoriteFood.user_id == user.id, FavoriteFood.food_id == food_id
        )
    )
    await session.commit()


async def add_favorite_cook(session: AsyncSession, user: User, cook_id: int) -> bool:
    cook = await session.get(User, cook_id)
    if cook is None or not cook.is_cook:
        return False
    existing = await session.execute(
        select(FavoriteCook.id).where(
            FavoriteCook.user_id == user.id, FavoriteCook.cook_id == cook_id
        )
    )
    if existing.first() is None:
        session.add(FavoriteCook(user_id=user.id, cook_id=cook_id))
        await session.commit()
    return True


async def remove_favorite_cook(session: AsyncSession, user: User, cook_id: int) -> None:
    await session.execute(
        delete(FavoriteCook).where(
            FavoriteCook.user_id == user.id, FavoriteCook.cook_id == cook_id
        )
    )
    await session.commit()


async def get_favorite_foods(session: AsyncSession, user: User) -> list[Food]:
    result = await session.execute(
        select(Food)
        .options(selectinload(Food.cook))
        .join(FavoriteFood, FavoriteFood.food_id == Food.id)
        .where(FavoriteFood.user_id == user.id)
        .order_by(FavoriteFood.created_at.desc())
    )
    return list(result.scalars().all())


async def get_favorite_cooks(session: AsyncSession, user: User) -> list[User]:
    result = await session.execute(
        select(User)
        .join(FavoriteCook, FavoriteCook.cook_id == User.id)
        .where(FavoriteCook.user_id == user.id)
        .order_by(FavoriteCook.created_at.desc())
    )
    return list(result.scalars().all())


async def get_favorite_food_ids(session: AsyncSession, user: User) -> set[int]:
    result = await session.execute(
        select(FavoriteFood.food_id).where(FavoriteFood.user_id == user.id)
    )
    return {row[0] for row in result.all()}


async def get_favorite_cook_ids(session: AsyncSession, user: User) -> set[int]:
    result = await session.execute(
        select(FavoriteCook.cook_id).where(FavoriteCook.user_id == user.id)
    )
    return {row[0] for row in result.all()}
