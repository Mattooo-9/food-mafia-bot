from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import (
    CategoriesOut,
    CookProfileIn,
    CurrencyOut,
    LocationIn,
    OkOut,
    ReferralOut,
    SearchHistoryOut,
    UserInsightsOut,
    UserOut,
    UserPreferencesIn,
    WalletIn,
)
from backend.config import settings
from backend.services import insights_service, referral_service, search_history_service, user_service
from backend.services.user_service import WalletError
from backend.utils.categories import tree_for_api, all_paths

router = APIRouter(tags=["users"])


@router.get("/me/insights", response_model=UserInsightsOut)
async def my_insights(user: CurrentUser, session: SessionDep) -> UserInsightsOut:
    return UserInsightsOut(**await insights_service.user_insights(session, user))


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/me/location", response_model=UserOut)
async def set_location(payload: LocationIn, user: CurrentUser, session: SessionDep) -> UserOut:
    updated = await user_service.update_location(session, user, payload.lat, payload.lon)
    return UserOut.model_validate(updated)


@router.post("/me/preferences", response_model=UserOut)
async def set_preferences(
    payload: UserPreferencesIn, user: CurrentUser, session: SessionDep
) -> UserOut:
    updated = await user_service.update_preferences(
        session, user, locale=payload.locale, timezone=payload.timezone
    )
    return UserOut.model_validate(updated)


@router.post("/me/onboarding", response_model=UserOut)
async def finish_onboarding(user: CurrentUser, session: SessionDep) -> UserOut:
    updated = await user_service.complete_onboarding(session, user)
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
    from backend.api.schemas import CategoryGroupOut, CategoryItemOut

    groups = [
        CategoryGroupOut(
            group=g["group"],
            categories=[CategoryItemOut(name=c["name"], subgroups=c["subgroups"]) for c in g["categories"]],
        )
        for g in tree_for_api()
    ]
    return CategoriesOut(groups=groups, flat=all_paths())


@router.get("/me/searches", response_model=list[SearchHistoryOut])
async def my_searches(user: CurrentUser, session: SessionDep) -> list[SearchHistoryOut]:
    rows = await search_history_service.list_searches(session, user.id)
    return [SearchHistoryOut.model_validate(r) for r in rows]


@router.delete("/me/privacy", response_model=OkOut)
async def wipe_privacy_data(user: CurrentUser, session: SessionDep) -> OkOut:
    from backend.services import memory_service

    await search_history_service.clear_searches(session, user.id)
    await memory_service.clear_memory(session, user.id)
    return OkOut()


@router.delete("/me/searches", response_model=OkOut)
async def clear_my_searches(user: CurrentUser, session: SessionDep) -> OkOut:
    from backend.services import memory_service

    await search_history_service.clear_searches(session, user.id)
    await memory_service.clear_memory(session, user.id)
    return OkOut()
