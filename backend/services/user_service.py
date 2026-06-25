from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import referral_service
from backend.utils.locale_tz import fuzz_coordinate, infer_timezone, normalize_locale
from backend.utils.telegram_auth import TelegramUser
from backend.utils.ton import is_valid_ton_address


def _apply_tg_profile(user: User, tg_user: TelegramUser) -> bool:
    changed = False
    if user.username != tg_user.username:
        user.username = tg_user.username
        changed = True
    if tg_user.first_name and user.first_name != tg_user.first_name:
        user.first_name = tg_user.first_name
        changed = True
    if tg_user.language_code and user.language_code != tg_user.language_code:
        user.language_code = tg_user.language_code
        changed = True
        if user.locale == "ru" or not user.locale:
            user.locale = normalize_locale(tg_user.language_code, user.locale)
        user.timezone = infer_timezone(
            timezone_name=user.timezone,
            language_code=tg_user.language_code,
            lat=user.lat,
            lon=user.lon,
        )
    return changed


async def get_or_create_user(
    session: AsyncSession, tg_user: TelegramUser, ref_code: str | None = None
) -> tuple[User, bool]:
    user = await get_user_by_tg_id(session, tg_user.tg_id)
    if user is None:
        locale = normalize_locale(tg_user.language_code, None)
        user = User(
            tg_id=tg_user.tg_id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language_code=tg_user.language_code,
            locale=locale,
            timezone=infer_timezone(language_code=tg_user.language_code),
            wellness_consent=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        if ref_code:
            await referral_service.attach_referrer(session, user, ref_code)
        await referral_service.ensure_referral_code(session, user)
        return user, True

    if _apply_tg_profile(user, tg_user):
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
    user.lat = fuzz_coordinate(lat)
    user.lon = fuzz_coordinate(lon)
    user.timezone = infer_timezone(
        timezone_name=user.timezone,
        language_code=user.language_code,
        lat=user.lat,
        lon=user.lon,
    )
    user.onboarding_done = True
    await session.commit()
    return user


async def update_preferences(
    session: AsyncSession,
    user: User,
    *,
    locale: str | None = None,
    timezone: str | None = None,
) -> User:
    if locale is not None:
        user.locale = normalize_locale(user.language_code, locale)
    if timezone is not None and timezone.strip():
        user.timezone = infer_timezone(timezone_name=timezone.strip(), language_code=user.language_code)
    await session.commit()
    return user


async def complete_onboarding(session: AsyncSession, user: User) -> User:
    user.onboarding_done = True
    await session.commit()
    return user


class WalletError(Exception):
    pass


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


async def update_wellness(
    session: AsyncSession,
    user: User,
    *,
    consent: bool | None = None,
    diet_preference: str | None = None,
    activity_level: str | None = None,
) -> User:
    from datetime import datetime, timezone

    valid_activity = {"sedentary", "light", "moderate", "active", "intense"}
    if consent is not None:
        user.wellness_consent = consent
        user.wellness_consent_at = datetime.now(timezone.utc) if consent else None
    if diet_preference is not None:
        user.diet_preference = diet_preference.strip()[:256] or None
    if activity_level is not None:
        level = activity_level.strip().lower()
        if level in valid_activity:
            user.activity_level = level
    await session.commit()
    return user
