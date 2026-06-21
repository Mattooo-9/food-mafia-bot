from fastapi import APIRouter, HTTPException, Query

from backend.api.deps import CurrentCook, CurrentUser, SessionDep
from backend.api.schemas import FoodIn, FoodOut, FoodUpdateIn, OkOut
from backend.api.serializers import serialize_food
from backend.services import favorite_service, food_service, notification_service
from backend.services.food_service import FEED_TYPES, FoodError
from backend.utils.geo import haversine_m

router = APIRouter(tags=["foods"])


@router.get("/foods", response_model=list[FoodOut])
async def list_foods(
    user: CurrentUser,
    session: SessionDep,
    feed: str = Query(default="nearby"),
    q: str | None = Query(default=None, max_length=128),
    category: str | None = None,
    max_distance_m: float | None = Query(default=None, ge=100, le=100_000),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FoodOut]:
    if feed not in FEED_TYPES:
        raise HTTPException(status_code=422, detail="Неизвестный тип ленты")
    items = await food_service.search_foods(
        session,
        user,
        feed=feed,
        category=category,
        q=q,
        max_distance_m=max_distance_m,
        price_min=price_min,
        price_max=price_max,
        min_rating=min_rating,
        limit=limit,
        offset=offset,
    )
    favorite_ids = await favorite_service.get_favorite_food_ids(session, user)
    return [serialize_food(i.food, i.distance_m, favorite_ids) for i in items]


@router.get("/foods/{food_id}", response_model=FoodOut)
async def get_food(food_id: int, user: CurrentUser, session: SessionDep) -> FoodOut:
    food = await food_service.get_food(session, food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    distance = None
    cook = food.cook
    if None not in (user.lat, user.lon, cook.lat, cook.lon):
        distance = haversine_m(user.lat, user.lon, cook.lat, cook.lon)
    favorite_ids = await favorite_service.get_favorite_food_ids(session, user)
    return serialize_food(food, distance, favorite_ids)


@router.get("/cook/foods", response_model=list[FoodOut])
async def my_foods(cook: CurrentCook, session: SessionDep) -> list[FoodOut]:
    foods = await food_service.get_cook_foods(session, cook.id, include_inactive=True)
    return [serialize_food(f) for f in foods]


@router.post("/cook/foods", response_model=FoodOut)
async def create_food(payload: FoodIn, cook: CurrentCook, session: SessionDep) -> FoodOut:
    try:
        food = await food_service.create_food(
            session,
            cook,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            category=payload.category,
            portions=payload.portions,
            cooking_time_minutes=payload.cooking_time_minutes,
            photo=payload.photo,
        )
    except FoodError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    food = await food_service.get_food(session, food.id)
    await notification_service.notify_subscribers_new_food(session, food, cook)
    return serialize_food(food)


@router.patch("/cook/foods/{food_id}", response_model=FoodOut)
async def update_food(
    food_id: int, payload: FoodUpdateIn, cook: CurrentCook, session: SessionDep
) -> FoodOut:
    try:
        food = await food_service.update_food(
            session, cook, food_id, payload.model_dump(exclude_unset=True)
        )
    except FoodError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_food(food)


@router.delete("/cook/foods/{food_id}", response_model=OkOut)
async def delete_food(food_id: int, cook: CurrentCook, session: SessionDep) -> OkOut:
    try:
        await food_service.delete_food(session, cook, food_id)
    except FoodError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OkOut()
