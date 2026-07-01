from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_session
from backend.i18n.messages import t
from backend.models import User
from backend.services import user_service
from backend.services.deductive_service import sync_user_profile
from backend.utils.locale_tz import infer_timezone, normalize_locale as tz_normalize
from backend.utils.telegram_auth import InitDataError, parse_start_param, validate_init_data

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
    x_client_timezone: Annotated[str | None, Header()] = None,
    x_client_locale: Annotated[str | None, Header()] = None,
) -> User:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Open via Telegram")

    try:
        tg_user = validate_init_data(
            x_telegram_init_data,
            settings.bot_token,
            settings.init_data_max_age_seconds,
        )
    except InitDataError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    ref_code: str | None = None
    start = parse_start_param(x_telegram_init_data)
    if start and start.startswith("ref_"):
        ref_code = start[4:]

    user, _ = await user_service.get_or_create_user(session, tg_user, ref_code)

    if x_client_locale and x_client_locale.strip():
        loc = tz_normalize(tg_user.language_code, x_client_locale.strip())
        if user.locale != loc:
            user.locale = loc
            await session.commit()

    user = await sync_user_profile(session, user)

    if x_client_timezone and x_client_timezone.strip():
        tz = infer_timezone(
            timezone_name=x_client_timezone.strip(),
            language_code=user.language_code,
            lat=user.lat,
            lon=user.lon,
        )
        if tz != user.timezone:
            user.timezone = tz
            await session.commit()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_cook(user: CurrentUser) -> User:
    if not user.is_cook:
        raise HTTPException(status_code=403, detail="Cook access only")
    return user


CurrentCook = Annotated[User, Depends(get_current_cook)]
