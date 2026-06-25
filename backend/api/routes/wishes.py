from fastapi import APIRouter, HTTPException, Query

from backend.api.deps import CurrentCook, CurrentUser, SessionDep
from backend.api.schemas import OkOut, OrderWishIn, OrderWishOut, RecipeHintsOut, WellnessIn, WellnessOut
from backend.api.serializers import serialize_order_wish
from backend.services import nutrition_service, order_wish_service
from backend.services.order_wish_service import OrderWishError
from backend.services import user_service

router = APIRouter(tags=["wishes"])


@router.post("/wishes", response_model=OrderWishOut)
async def create_wish(payload: OrderWishIn, user: CurrentUser, session: SessionDep) -> OrderWishOut:
    try:
        wish = await order_wish_service.create_wish(
            session,
            user,
            payload.title,
            payload.details,
            budget_max=payload.budget_max,
            portions=payload.portions,
        )
    except OrderWishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order_wish(wish, viewer=user)


@router.get("/wishes", response_model=list[OrderWishOut])
async def my_wishes(user: CurrentUser, session: SessionDep) -> list[OrderWishOut]:
    wishes = await order_wish_service.list_buyer_wishes(session, user)
    return [serialize_order_wish(w, viewer=user) for w in wishes]


@router.get("/cook/wishes/mine", response_model=list[OrderWishOut])
async def my_claimed_wishes(cook: CurrentCook, session: SessionDep) -> list[OrderWishOut]:
    wishes = await order_wish_service.list_cook_claimed_wishes(session, cook)
    return [serialize_order_wish(w, viewer=cook) for w in wishes]


@router.get("/cook/wishes", response_model=list[OrderWishOut])
async def open_wishes_for_cook(
    cook: CurrentCook,
    session: SessionDep,
    max_distance_m: float | None = Query(default=15000, ge=500),
) -> list[OrderWishOut]:
    items = await order_wish_service.list_open_wishes(session, cook, max_distance_m=max_distance_m)
    return [serialize_order_wish(w, distance_m=d, viewer=cook) for w, d in items]


@router.post("/wishes/{wish_id}/claim", response_model=OrderWishOut)
async def claim_wish(wish_id: int, cook: CurrentCook, session: SessionDep) -> OrderWishOut:
    try:
        wish = await order_wish_service.claim_wish(session, cook, wish_id)
    except OrderWishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order_wish(wish, viewer=cook)


@router.post("/wishes/{wish_id}/cancel", response_model=OrderWishOut)
async def cancel_wish(wish_id: int, user: CurrentUser, session: SessionDep) -> OrderWishOut:
    try:
        wish = await order_wish_service.cancel_wish(session, user, wish_id)
    except OrderWishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order_wish(wish, viewer=user)


@router.post("/wishes/{wish_id}/complete", response_model=OrderWishOut)
async def complete_wish(wish_id: int, cook: CurrentCook, session: SessionDep) -> OrderWishOut:
    try:
        wish = await order_wish_service.complete_wish(session, cook, wish_id)
    except OrderWishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order_wish(wish, viewer=cook)


@router.post("/me/wellness", response_model=WellnessOut)
async def set_wellness(payload: WellnessIn, user: CurrentUser, session: SessionDep) -> WellnessOut:
    updated = await user_service.update_wellness(
        session,
        user,
        consent=payload.consent,
        diet_preference=payload.diet_preference,
        activity_level=payload.activity_level,
    )
    snap = await nutrition_service.wellness_tip(session, updated)
    return WellnessOut(**nutrition_service.wellness_response(updated, snap))


@router.post("/me/wellness/water", response_model=WellnessOut)
async def log_water(user: CurrentUser, session: SessionDep) -> WellnessOut:
    from backend.services.wellness_tracker import log_water as track_water

    await track_water(session, user)
    await session.commit()
    snap = await nutrition_service.wellness_tip(session, user)
    return WellnessOut(**nutrition_service.wellness_response(user, snap))


@router.get("/ai/wellness", response_model=WellnessOut)
async def get_wellness(user: CurrentUser, session: SessionDep) -> WellnessOut:
    snap = await nutrition_service.wellness_tip(session, user)
    return WellnessOut(**nutrition_service.wellness_response(user, snap))


@router.get("/cook/recipe-hints", response_model=RecipeHintsOut)
async def cook_recipe_hints(
    cook: CurrentCook,
    session: SessionDep,
    q: str = Query(default="", max_length=256),
) -> RecipeHintsOut:
    hints = await nutrition_service.recipe_hints_for_cook(session, cook, context=q)
    return RecipeHintsOut(hints=hints)
