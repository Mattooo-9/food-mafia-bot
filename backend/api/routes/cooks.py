from fastapi import APIRouter, HTTPException, Query

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import CookOut, FoodOut, ReviewOut
from backend.api.serializers import serialize_cook, serialize_food, serialize_review
from backend.services import favorite_service, food_service, review_service, subscription_service
from backend.services import user_service
from backend.utils.geo import haversine_m

router = APIRouter(tags=["cooks"])


@router.get("/cooks", response_model=list[CookOut])
async def list_cooks(
    user: CurrentUser,
    session: SessionDep,
    max_distance_m: float | None = Query(default=None, ge=100, le=100_000),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    q: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CookOut]:
    items = await food_service.search_cooks(
        session, user, q=q, max_distance_m=max_distance_m, min_rating=min_rating, limit=limit, offset=offset
    )
    favorite_ids = await favorite_service.get_favorite_cook_ids(session, user)
    subscribed_ids = await subscription_service.get_subscription_cook_ids(session, user)
    return [serialize_cook(cook, dist, favorite_ids, subscribed_ids) for cook, dist in items]


@router.get("/cooks/{cook_id}", response_model=CookOut)
async def get_cook(cook_id: int, user: CurrentUser, session: SessionDep) -> CookOut:
    cook = await user_service.get_user_by_id(session, cook_id)
    if cook is None or not cook.is_cook:
        raise HTTPException(status_code=404, detail="Повар не найден")
    distance = None
    if None not in (user.lat, user.lon, cook.lat, cook.lon):
        distance = haversine_m(user.lat, user.lon, cook.lat, cook.lon)
    favorite_ids = await favorite_service.get_favorite_cook_ids(session, user)
    subscribed_ids = await subscription_service.get_subscription_cook_ids(session, user)
    return serialize_cook(cook, distance, favorite_ids, subscribed_ids)


@router.get("/cooks/{cook_id}/foods", response_model=list[FoodOut])
async def get_cook_foods(cook_id: int, user: CurrentUser, session: SessionDep) -> list[FoodOut]:
    cook = await user_service.get_user_by_id(session, cook_id)
    if cook is None or not cook.is_cook:
        raise HTTPException(status_code=404, detail="Повар не найден")
    foods = await food_service.get_cook_foods(session, cook_id, include_inactive=False)
    favorite_ids = await favorite_service.get_favorite_food_ids(session, user)
    distance = None
    if None not in (user.lat, user.lon, cook.lat, cook.lon):
        distance = haversine_m(user.lat, user.lon, cook.lat, cook.lon)
    return [serialize_food(f, distance, favorite_ids) for f in foods]


@router.get("/cooks/{cook_id}/reviews", response_model=list[ReviewOut])
async def get_cook_reviews(cook_id: int, user: CurrentUser, session: SessionDep) -> list[ReviewOut]:
    reviews = await review_service.get_cook_reviews(session, cook_id)
    return [serialize_review(r, viewer=user) for r in reviews]
