from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import FOOD_CATEGORIES, Food, User
from backend.services.pricing_engine import auto_ingredients_text, infer_cooking_minutes
from backend.utils.geo import haversine_m


class FoodError(Exception):
    pass


@dataclass
class FoodWithDistance:
    food: Food
    distance_m: float | None


FEED_TYPES = ["cheap", "fast", "nearby", "new", "popular"]


async def create_food(
    session: AsyncSession,
    cook: User,
    name: str,
    description: str,
    price: float,
    category: str,
    portions: int,
    cooking_time_minutes: int,
    photo: str | None,
    ingredients: str = "",
) -> Food:
    if not cook.is_cook:
        raise FoodError("Сначала создайте профиль повара")
    if category not in FOOD_CATEGORIES:
        raise FoodError("Неизвестная категория")
    auto_ing = auto_ingredients_text(name, description, category)
    food = Food(
        cook_id=cook.id,
        name=name.strip(),
        description=description.strip(),
        price=round(price, 2),
        category=category,
        portions=portions,
        cooking_time_minutes=cooking_time_minutes or infer_cooking_minutes(category),
        photo=photo,
        ingredients=(ingredients.strip() or auto_ing)[:2000],
    )
    session.add(food)
    await session.commit()
    await session.refresh(food)
    return food


async def update_food(session: AsyncSession, cook: User, food_id: int, data: dict) -> Food:
    food = await get_food(session, food_id)
    if food is None or food.cook_id != cook.id:
        raise FoodError("Блюдо не найдено")
    if "category" in data and data["category"] not in FOOD_CATEGORIES:
        raise FoodError("Неизвестная категория")
    for field in (
        "name",
        "description",
        "price",
        "category",
        "portions",
        "cooking_time_minutes",
        "is_active",
        "photo",
        "ingredients",
    ):
        if field in data and data[field] is not None:
            value = data[field]
            if field == "price":
                value = round(float(value), 2)
            if field in ("name", "description", "ingredients"):
                value = str(value).strip()
            setattr(food, field, value)
    if "name" in data or "description" in data:
        food.ingredients = auto_ingredients_text(food.name, food.description, food.category)[:2000]
    await session.commit()
    await session.refresh(food)
    return food


async def delete_food(session: AsyncSession, cook: User, food_id: int) -> None:
    food = await get_food(session, food_id)
    if food is None or food.cook_id != cook.id:
        raise FoodError("Блюдо не найдено")
    await session.delete(food)
    await session.commit()


async def get_food(session: AsyncSession, food_id: int) -> Food | None:
    result = await session.execute(
        select(Food).options(selectinload(Food.cook)).where(Food.id == food_id)
    )
    return result.scalar_one_or_none()


async def get_cook_foods(session: AsyncSession, cook_id: int, include_inactive: bool) -> list[Food]:
    query = select(Food).options(selectinload(Food.cook)).where(Food.cook_id == cook_id)
    if not include_inactive:
        query = query.where(Food.is_active.is_(True))
    query = query.order_by(Food.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


async def search_foods(
    session: AsyncSession,
    viewer: User,
    feed: str = "nearby",
    category: str | None = None,
    q: str | None = None,
    max_distance_m: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    min_rating: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FoodWithDistance]:
    query = (
        select(Food)
        .options(selectinload(Food.cook))
        .join(User, Food.cook_id == User.id)
        .where(
            Food.is_active.is_(True),
            Food.portions > 0,
            User.is_cook.is_(True),
            User.is_online.is_(True),
        )
    )
    if category:
        query = query.where(Food.category == category)
    if price_min is not None:
        query = query.where(Food.price >= price_min)
    if price_max is not None:
        query = query.where(Food.price <= price_max)
    if min_rating is not None:
        query = query.where(User.rating_avg >= min_rating)
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Food.name).like(needle),
                func.lower(Food.description).like(needle),
                func.lower(User.cook_name).like(needle),
                func.lower(User.first_name).like(needle),
            )
        )

    result = await session.execute(query)
    foods = list(result.scalars().all())

    items: list[FoodWithDistance] = []
    has_location = viewer.lat is not None and viewer.lon is not None
    for food in foods:
        distance: float | None = None
        cook = food.cook
        if has_location and cook.lat is not None and cook.lon is not None:
            distance = haversine_m(viewer.lat, viewer.lon, cook.lat, cook.lon)
        if max_distance_m is not None:
            if distance is None or distance > max_distance_m:
                continue
        items.append(FoodWithDistance(food=food, distance_m=distance))

    far = float("inf")
    if q and q.strip():
        needle = q.strip().lower()
        items.sort(
            key=lambda i: (
                0 if needle in i.food.name.lower() else 1,
                i.distance_m if i.distance_m is not None else far,
            )
        )
    elif feed == "nearby":
        items.sort(key=lambda i: i.distance_m if i.distance_m is not None else far)
    elif feed == "new":
        items.sort(key=lambda i: i.food.created_at, reverse=True)
    elif feed == "popular":
        items.sort(key=lambda i: (i.food.orders_count, i.food.cook.rating_avg), reverse=True)
    elif feed == "cheap":
        items.sort(key=lambda i: i.food.price)
    elif feed == "fast":
        items.sort(key=lambda i: i.food.cooking_time_minutes)
    else:
        raise FoodError("Неизвестный тип ленты")

    return items[offset : offset + limit]


async def search_cooks(
    session: AsyncSession,
    viewer: User,
    q: str | None = None,
    max_distance_m: float | None = None,
    min_rating: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[tuple[User, float | None]]:
    query = select(User).where(User.is_cook.is_(True), User.is_online.is_(True))
    if min_rating is not None:
        query = query.where(User.rating_avg >= min_rating)
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(User.cook_name).like(needle),
                func.lower(User.first_name).like(needle),
                func.lower(User.cook_description).like(needle),
            )
        )
    result = await session.execute(query)
    cooks = list(result.scalars().all())

    has_location = viewer.lat is not None and viewer.lon is not None
    items: list[tuple[User, float | None]] = []
    for cook in cooks:
        distance: float | None = None
        if has_location and cook.lat is not None and cook.lon is not None:
            distance = haversine_m(viewer.lat, viewer.lon, cook.lat, cook.lon)
        if max_distance_m is not None:
            if distance is None or distance > max_distance_m:
                continue
        items.append((cook, distance))

    items.sort(key=lambda i: i[1] if i[1] is not None else float("inf"))
    return items[offset : offset + limit]
