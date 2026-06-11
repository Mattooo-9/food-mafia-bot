from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import CookOut, FoodOut, OkOut
from backend.api.serializers import serialize_cook, serialize_food
from backend.services import favorite_service, subscription_service
from backend.utils.geo import haversine_m

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/foods", response_model=list[FoodOut])
async def favorite_foods(user: CurrentUser, session: SessionDep) -> list[FoodOut]:
    foods = await favorite_service.get_favorite_foods(session, user)
    result = []
    for food in foods:
        distance = None
        cook = food.cook
        if None not in (user.lat, user.lon, cook.lat, cook.lon):
            distance = haversine_m(user.lat, user.lon, cook.lat, cook.lon)
        out = serialize_food(food, distance)
        out.is_favorite = True
        result.append(out)
    return result


@router.get("/cooks", response_model=list[CookOut])
async def favorite_cooks(user: CurrentUser, session: SessionDep) -> list[CookOut]:
    cooks = await favorite_service.get_favorite_cooks(session, user)
    subscribed_ids = await subscription_service.get_subscription_cook_ids(session, user)
    result = []
    for cook in cooks:
        distance = None
        if None not in (user.lat, user.lon, cook.lat, cook.lon):
            distance = haversine_m(user.lat, user.lon, cook.lat, cook.lon)
        out = serialize_cook(cook, distance, subscribed_ids=subscribed_ids)
        out.is_favorite = True
        result.append(out)
    return result


@router.post("/foods/{food_id}", response_model=OkOut)
async def add_favorite_food(food_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    ok = await favorite_service.add_favorite_food(session, user, food_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    return OkOut()


@router.delete("/foods/{food_id}", response_model=OkOut)
async def remove_favorite_food(food_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    await favorite_service.remove_favorite_food(session, user, food_id)
    return OkOut()


@router.post("/cooks/{cook_id}", response_model=OkOut)
async def add_favorite_cook(cook_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    ok = await favorite_service.add_favorite_cook(session, user, cook_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Повар не найден")
    return OkOut()


@router.delete("/cooks/{cook_id}", response_model=OkOut)
async def remove_favorite_cook(cook_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    await favorite_service.remove_favorite_cook(session, user, cook_id)
    return OkOut()
