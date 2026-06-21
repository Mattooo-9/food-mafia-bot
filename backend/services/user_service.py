from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import referral_service
from backend.utils.telegram_auth import TelegramUser
from backend.utils.ton import is_valid_ton_address


class WalletError(Exception):
    pass


async def get_or_create_user(
    session: AsyncSession, tg_user: TelegramUser, ref_code: str | None = None
) -> tuple[User, bool]:
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
        if ref_code:
            await referral_service.attach_referrer(session, user, ref_code)
        await referral_service.ensure_referral_code(session, user)
        return user, True

    changed = False
    if user.username != tg_user.username:
        user.username = tg_user.username
        changed = True
    if tg_user.first_name and user.first_name != tg_user.first_name:
        user.first_name = tg_user.first_name
        changed = True
    if changed:
        await session.commit()
    if ref_code and user.referred_by_id is None:
        await referral_service.attach_referrer(session, user, ref_code)
    await referral_service.ensure_referral_code(session, user)
    return user, False


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


async def update_wallet(
    session: AsyncSession, user: User, ton_wallet_address: str | None
) -> User:
    if ton_wallet_address is None or not ton_wallet_address.strip():
        user.ton_wallet_address = None
    else:
        address = ton_wallet_address.strip()
        if not is_valid_ton_address(address):
            raise WalletError("Некорректный TON-адрес. Подключите кошелёк через TON Connect.")
        user.ton_wallet_address = address
    await session.commit()
    return user
