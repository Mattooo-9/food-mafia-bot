from fastapi import APIRouter

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import CategoriesOut, CookProfileIn, LocationIn, UserOut
from backend.services import user_service

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


@router.get("/categories", response_model=CategoriesOut)
async def get_categories() -> CategoriesOut:
    return CategoriesOut()
