"""Market data aggregation from the live database (no external APIs)."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Food, Order, OrderStatus, Review, User
from backend.utils.geo import haversine_m


@dataclass
class CategoryStats:
    category: str
    dish_count: int
    order_volume: int
    avg_price: float
    median_price: float
    min_price: float
    max_price: float
    avg_rating: float
    avg_orders_per_dish: float
    review_sentiment: float  # -1..1


@dataclass
class MarketOverview:
    total_dishes: int
    total_orders: int
    avg_price: float
    median_price: float
    avg_rating: float
    top_category: str
    categories: list[CategoryStats]


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def _region_key(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "global"
    return f"{round(lat, 1)}_{round(lon, 1)}"


async def _active_foods_in_radius(
    session: AsyncSession,
    lat: float | None,
    lon: float | None,
    radius_m: float,
) -> list[tuple[Food, User, float | None]]:
    result = await session.execute(
        select(Food, User)
        .join(User, Food.cook_id == User.id)
        .where(
            Food.is_active.is_(True),
            Food.portions > 0,
            User.is_cook.is_(True),
            User.is_online.is_(True),
        )
    )
    rows = result.all()
    items: list[tuple[Food, User, float | None]] = []
    for food, cook in rows:
        dist: float | None = None
        if lat is not None and lon is not None and cook.lat is not None and cook.lon is not None:
            dist = haversine_m(lat, lon, cook.lat, cook.lon)
            if dist > radius_m:
                continue
        items.append((food, cook, dist))
    return items


_POSITIVE = {
    "вкус", "отлич", "супер", "рекоменд", "класс", "прекрас", "восхит", "норм",
    "хорош", "спасиб", "топ", "люблю", "свеж", "домашн",
}
_NEGATIVE = {"плох", "ужас", "холод", "несвеж", "жалоб", "разочар", "не рекоменд", "отрав"}


def review_sentiment_score(texts: list[str]) -> float:
    if not texts:
        return 0.0
    score = 0
    for text in texts:
        low = text.lower()
        pos = sum(1 for w in _POSITIVE if w in low)
        neg = sum(1 for w in _NEGATIVE if w in low)
        score += pos - neg
    return max(-1.0, min(1.0, score / max(len(texts), 1)))


async def compute_category_stats(
    session: AsyncSession,
    foods_with_cooks: list[tuple[Food, User, float | None]],
) -> list[CategoryStats]:
    by_cat: dict[str, list[tuple[Food, User]]] = {}
    for food, cook, _ in foods_with_cooks:
        by_cat.setdefault(food.category, []).append((food, cook))

    review_rows = await session.execute(select(Review.text).where(Review.text != ""))
    all_review_texts = [r[0] for r in review_rows.all()]
    sentiment = review_sentiment_score(all_review_texts)

    stats_list: list[CategoryStats] = []
    for category, pairs in by_cat.items():
        prices = [f.price for f, _ in pairs]
        orders = sum(f.orders_count for f, _ in pairs)
        ratings = [c.rating_avg for _, c in pairs if c.rating_count > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        stats_list.append(
            CategoryStats(
                category=category,
                dish_count=len(pairs),
                order_volume=orders,
                avg_price=round(sum(prices) / len(prices), 2),
                median_price=round(_median(prices), 2),
                min_price=round(min(prices), 2),
                max_price=round(max(prices), 2),
                avg_rating=round(avg_rating, 2),
                avg_orders_per_dish=round(orders / max(len(pairs), 1), 2),
                review_sentiment=sentiment,
            )
        )
    return stats_list


async def get_market_overview(
    session: AsyncSession,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float = 10_000,
) -> MarketOverview:
    items = await _active_foods_in_radius(session, lat, lon, radius_m)
    categories = await compute_category_stats(session, items)

    if not items:
        delivered = await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED.value)
        )
        return MarketOverview(
            total_dishes=0,
            total_orders=int(delivered.scalar_one() or 0),
            avg_price=0,
            median_price=0,
            avg_rating=0,
            top_category="—",
            categories=[],
        )

    prices = [f.price for f, _, _ in items]
    ratings = [c.rating_avg for _, c, _ in items if c.rating_count > 0]
    total_orders = sum(f.orders_count for f, _, _ in items)
    top = max(categories, key=lambda c: c.order_volume) if categories else None

    return MarketOverview(
        total_dishes=len(items),
        total_orders=total_orders,
        avg_price=round(sum(prices) / len(prices), 2),
        median_price=round(_median(prices), 2),
        avg_rating=round(sum(ratings) / len(ratings), 2) if ratings else 0,
        top_category=top.category if top else "—",
        categories=categories,
    )


def demand_index(stats: CategoryStats) -> float:
    """0–100 demand score from orders and competition."""
    if stats.dish_count == 0:
        return 0.0
    per_dish = stats.avg_orders_per_dish
    competition_penalty = min(40, stats.dish_count * 2)
    raw = min(100, per_dish * 15 + 30 + stats.review_sentiment * 10)
    return round(max(0, raw - competition_penalty * 0.3), 1)


def competition_index(dish_count: int) -> float:
    return round(min(100, dish_count * 8), 1)
