from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.utils.telegram_auth import TelegramUser


async def get_or_create_user(session: AsyncSession, tg_user: TelegramUser) -> User:
    user = await get_user_by_tg_id(session, tg_user.tg_id)
    if user is None:
        user = User(
            tg_id=tg_user.tg_id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    changed = False
    if user.username != tg_user.username:
        user.username = tg_user.username
        changed = True
    if tg_user.first_name and user.first_name != tg_user.first_name:
        user.first_name = tg_user.first_name
        changed = True
    if changed:
        await session.commit()
    return user


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def update_location(session: AsyncSession, user: User, lat: float, lon: float) -> User:
    user.lat = lat
    user.lon = lon
    await session.commit()
    return user


async def update_cook_profile(
    session: AsyncSession,
    user: User,
    cook_name: str | None = None,
    cook_description: str | None = None,
    cook_photo: str | None = None,
    is_online: bool | None = None,
) -> User:
    user.is_cook = True
    if cook_name is not None:
        user.cook_name = cook_name.strip()
    if cook_description is not None:
        user.cook_description = cook_description.strip()
    if cook_photo is not None:
        user.cook_photo = cook_photo
    if is_online is not None:
        user.is_online = is_online
    await session.commit()
    return user
