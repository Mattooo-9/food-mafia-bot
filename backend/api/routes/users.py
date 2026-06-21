from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import CategoriesOut, CookProfileIn, CurrencyOut, LocationIn, ReferralOut, UserOut, WalletIn
from backend.config import settings
from backend.services import referral_service, user_service
from backend.services.user_service import WalletError

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/me/location", response_model=UserOut)
async def set_location(payload: LocationIn, user: CurrentUser, session: SessionDep) -> UserOut:
    updated = await user_service.update_location(session, user, payload.lat, payload.lon)
    return UserOut.model_validate(updated)


@router.post("/me/cook-profile", response_model=UserOut)
async def upsert_cook_profile(
    payload: CookProfileIn, user: CurrentUser, session: SessionDep
) -> UserOut:
    updated = await user_service.update_cook_profile(
        session,
        user,
        cook_name=payload.cook_name,
        cook_description=payload.cook_description,
        cook_photo=payload.cook_photo,
        is_online=payload.is_online,
    )
    return UserOut.model_validate(updated)


@router.get("/me/referral", response_model=ReferralOut)
async def get_my_referral(user: CurrentUser, session: SessionDep) -> ReferralOut:
    info = await referral_service.get_referral_info(session, user)
    return ReferralOut(**info)


@router.post("/me/wallet", response_model=UserOut)
async def set_wallet(payload: WalletIn, user: CurrentUser, session: SessionDep) -> UserOut:
    try:
        updated = await user_service.update_wallet(session, user, payload.ton_wallet_address)
    except WalletError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserOut.model_validate(updated)


@router.get("/currency", response_model=CurrencyOut)
async def get_currency() -> CurrencyOut:
    return CurrencyOut(ton_per_star=settings.ton_per_star)


@router.get("/categories", response_model=CategoriesOut)
async def get_categories() -> CategoriesOut:
    return CategoriesOut()
