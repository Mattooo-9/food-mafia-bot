"""Built-in AI market analyst: statistical scoring + natural-language insights."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models import Food, FoodEvaluation, MarketSnapshot, User
from backend.services import analytics_service, pricing_engine
from backend.services.analytics_service import CategoryStats, MarketOverview
from backend.services.pricing_engine import VERDICT_LABELS as PRICING_VERDICTS

logger = logging.getLogger(__name__)

VERDICT_LABELS = {
    **PRICING_VERDICTS,
    "underpriced": "Ниже рынка",
    "fair": "Справедливая цена",
    "premium": "Премиум",
    "overpriced": "Завышена",
}

TREND_LABELS = {
    "rising": "Рост спроса",
    "falling": "Снижение спроса",
    "stable": "Стабильный рынок",
}


def _price_verdict(price: float, median: float) -> tuple[str, int]:
    if median <= 0:
        return "fair", 75
    ratio = price / median
    if ratio < 0.78:
        return "underpriced", min(100, int(88 + (0.78 - ratio) * 40))
    if ratio <= 1.12:
        return "fair", int(100 - abs(ratio - 1.0) * 120)
    if ratio <= 1.38:
        return "premium", int(max(35, 75 - (ratio - 1.12) * 100))
    return "overpriced", int(max(10, 45 - (ratio - 1.38) * 80))


def _quality_score(cook: User, sentiment: float) -> int:
    base = int((cook.rating_avg / 5.0) * 70) if cook.rating_count > 0 else 45
    orders_boost = min(20, cook.rating_count * 2)
    sentiment_boost = int(sentiment * 10)
    return max(0, min(100, base + orders_boost + sentiment_boost))


def _demand_score(food: Food, stats: CategoryStats | None) -> int:
    if stats is None or stats.dish_count == 0:
        return 50
    relative = food.orders_count / max(stats.avg_orders_per_dish, 0.5)
    idx = analytics_service.demand_index(stats)
    personal = min(100, int(relative * 25 + 40))
    return int(personal * 0.6 + idx * 0.4)


def _build_food_summary(
    food: Food,
    cook: User,
    verdict: str,
    price_score: int,
    quality_score: int,
    demand_score: int,
    stats: CategoryStats | None,
) -> tuple[str, str]:
    verdict_ru = VERDICT_LABELS.get(verdict, verdict)
    cat_median = stats.median_price if stats else food.price
    lines = [
        f"«{food.name}» в категории «{food.category}»: {verdict_ru.lower()}.",
    ]
    if stats and stats.dish_count >= 3:
        diff_pct = int((food.price / cat_median - 1) * 100) if cat_median else 0
        if diff_pct > 5:
            lines.append(f"Цена на {diff_pct}% выше медианы рынка ({int(cat_median)} ⭐).")
        elif diff_pct < -5:
            lines.append(f"Цена на {abs(diff_pct)}% ниже медианы ({int(cat_median)} ⭐) — выгодное предложение.")
        else:
            lines.append(f"Цена близка к рынку (медиана {int(cat_median)} ⭐).")

    if cook.rating_count > 0:
        lines.append(f"Рейтинг повара {cook.rating_avg:.1f}/5 ({cook.rating_count} отзывов).")
    if food.orders_count > 0:
        lines.append(f"Заказали {food.orders_count} раз — {'высокий' if demand_score >= 65 else 'умеренный' if demand_score >= 40 else 'низкий'} спрос.")

    buyer_tip = "Хороший выбор по соотношению цены и качества."
    if verdict == "below_cost":
        buyer_tip = "Цена ниже себестоимости — повару может быть невыгодно."
    elif verdict == "underpriced" and quality_score >= 60:
        buyer_tip = "Выгодная цена при достойном качестве — рекомендуем попробовать."
    elif verdict == "overpriced":
        buyer_tip = "Цена выше рынка — сравните с похожими блюдами в ленте."
    elif quality_score >= 80:
        buyer_tip = "Высокий рейтинг повара — надёжный выбор."
    elif demand_score >= 70:
        buyer_tip = "Популярное блюдо — заказывают часто."

    overall = int(price_score * 0.35 + quality_score * 0.4 + demand_score * 0.25)
    lines.append(f"Общая оценка ИИ: {overall}/100.")
    return " ".join(lines), buyer_tip


def _build_market_summary(overview: MarketOverview, cat: CategoryStats) -> str:
    demand = analytics_service.demand_index(cat)
    trend = "rising" if demand >= 60 else "falling" if demand <= 35 else "stable"
    parts = [
        f"Категория «{cat.category}»: {cat.dish_count} блюд, медиана {int(cat.median_price)} ⭐.",
        f"Средний рейтинг {cat.avg_rating:.1f}/5, спрос {int(demand)}/100.",
        TREND_LABELS[trend] + ".",
    ]
    if cat.review_sentiment > 0.3:
        parts.append("Отзывы в целом положительные.")
    elif cat.review_sentiment < -0.3:
        parts.append("В отзывах встречаются жалобы — будьте внимательны к рейтингу.")
    if overview.total_dishes > 0:
        parts.append(f"В радиусе {int(settings.ai_market_radius_m / 1000)} км — {overview.total_dishes} активных предложений.")
    return " ".join(parts)


async def evaluate_food(
    session: AsyncSession,
    food: Food,
    cook: User,
    stats_by_cat: dict[str, CategoryStats],
) -> FoodEvaluation:
    stats = stats_by_cat.get(food.category)
    regional_avg = stats.avg_price if stats and stats.dish_count >= 2 else (stats.median_price if stats else 0)

    rec = pricing_engine.compute_fair_price(
        regional_avg,
        food.category,
        ingredients=food.ingredients or food.description,
        portions=max(food.portions, 1),
        cooking_time_minutes=food.cooking_time_minutes,
        current_price=food.price,
        region_label="регион" if cook.lat else "платформа",
        dish_name=food.name,
    )

    verdict, price_score = rec.verdict, rec.price_score
    sentiment = stats.review_sentiment if stats else 0.0
    quality_score = _quality_score(cook, sentiment)
    demand_score = _demand_score(food, stats)
    overall = int(price_score * 0.35 + quality_score * 0.4 + demand_score * 0.25)

    summary, buyer_tip = _build_food_summary(
        food, cook, verdict, price_score, quality_score, demand_score, stats
    )
    summary = f"{rec.summary} {summary}"

    existing = await session.execute(
        select(FoodEvaluation).where(FoodEvaluation.food_id == food.id)
    )
    ev = existing.scalar_one_or_none()
    if ev is None:
        ev = FoodEvaluation(food_id=food.id)
        session.add(ev)

    ev.price_score = price_score
    ev.quality_score = quality_score
    ev.demand_score = demand_score
    ev.overall_score = overall
    ev.verdict = verdict
    ev.fair_price = rec.fair_price
    ev.suggested_price_min = rec.suggested_price_min
    ev.suggested_price_max = rec.suggested_price_max
    ev.summary = summary
    ev.buyer_tip = rec.buyer_savings_hint or buyer_tip
    ev.updated_at = datetime.now(timezone.utc)
    return ev


async def refresh_market_data(session: AsyncSession) -> int:
    """Recompute and persist market snapshots + food evaluations."""
    from backend.services.analytics_service import region_key

    # Global overview
    overview = await analytics_service.get_market_overview(
        session, radius_m=settings.ai_market_radius_m
    )
    stats_by_cat = {c.category: c for c in overview.categories}

    await session.execute(delete(MarketSnapshot))

    regions: dict[str, tuple[float | None, float | None]] = {"global": (None, None)}
    cooks_result = await session.execute(
        select(User.lat, User.lon).where(
            User.is_cook.is_(True),
            User.is_online.is_(True),
            User.lat.isnot(None),
            User.lon.isnot(None),
        )
    )
    for lat, lon in cooks_result.all():
        rk = region_key(lat, lon)
        regions[rk] = (lat, lon)

    for rk, (lat, lon) in regions.items():
        reg_overview = await analytics_service.get_market_overview(
            session, lat, lon, settings.ai_market_radius_m
        )
        for cat in reg_overview.categories:
            demand = analytics_service.demand_index(cat)
            competition = analytics_service.competition_index(cat.dish_count)
            trend = "rising" if demand >= 60 else "falling" if demand <= 35 else "stable"
            session.add(
                MarketSnapshot(
                    category=cat.category,
                    region_key=rk,
                    dish_count=cat.dish_count,
                    order_volume=cat.order_volume,
                    avg_price=cat.avg_price,
                    median_price=cat.median_price,
                    min_price=cat.min_price,
                    max_price=cat.max_price,
                    avg_rating=cat.avg_rating,
                    demand_index=demand,
                    competition_index=competition,
                    summary=_build_market_summary(reg_overview, cat),
                    trend=trend,
                )
            )
        if rk == "global":
            stats_by_cat = {c.category: c for c in reg_overview.categories}

    result = await session.execute(
        select(Food, User)
        .join(User, Food.cook_id == User.id)
        .where(Food.is_active.is_(True), User.is_cook.is_(True))
    )
    count = 0
    for food, cook in result.all():
        await evaluate_food(session, food, cook, stats_by_cat)
        count += 1

    await session.commit()
    logger.info("AI market refresh: %s categories, %s dish evaluations", len(overview.categories), count)
    return count


async def get_cached_market(
    session: AsyncSession,
    category: str | None = None,
    region_key: str = "global",
) -> list[MarketSnapshot]:
    query = select(MarketSnapshot).where(MarketSnapshot.region_key == region_key)
    if category:
        query = query.where(MarketSnapshot.category == category)
    query = query.order_by(MarketSnapshot.demand_index.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_food_evaluation(session: AsyncSession, food_id: int) -> FoodEvaluation | None:
    result = await session.execute(
        select(FoodEvaluation).where(FoodEvaluation.food_id == food_id)
    )
    return result.scalar_one_or_none()


async def get_price_suggestion(
    session: AsyncSession,
    category: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    current_price: float | None = None,
    ingredients: str = "",
    portions: int = 1,
    cooking_time_minutes: int = 30,
    dish_name: str = "",
) -> dict:
    stats, region_label = await analytics_service.get_regional_category_stats(
        session,
        category,
        lat,
        lon,
        settings.ai_market_radius_m,
    )
    regional_avg = stats.avg_price if stats and stats.dish_count >= 2 else (
        stats.median_price if stats else 0
    )

    rec = pricing_engine.compute_fair_price(
        regional_avg,
        category,
        ingredients=ingredients,
        portions=portions,
        cooking_time_minutes=cooking_time_minutes,
        current_price=current_price,
        region_label=region_label,
        dish_name=dish_name,
    )

    return {
        "category": category,
        "fair_price": rec.fair_price,
        "suggested_price_min": rec.suggested_price_min,
        "suggested_price_max": rec.suggested_price_max,
        "verdict": rec.verdict,
        "verdict_label": VERDICT_LABELS.get(rec.verdict, rec.verdict),
        "price_score": rec.price_score,
        "summary": rec.summary,
        "regional_avg_price": rec.regional_avg_price,
        "seasonal_market_price": rec.seasonal_market_price,
        "season_name": rec.season_name,
        "season_factor": rec.season_factor,
        "ingredient_cost": rec.ingredient_cost,
        "labor_cost": rec.labor_cost,
        "cook_minimum": rec.cook_minimum,
        "cook_margin_percent": rec.cook_margin_percent,
        "region_label": rec.region_label,
        "ingredient_items": rec.ingredient_items,
        "buyer_savings_hint": rec.buyer_savings_hint,
    }


async def get_recommendations(
    session: AsyncSession,
    viewer: User,
    limit: int = 10,
) -> list[tuple[Food, FoodEvaluation, float | None]]:
    from backend.services.food_service import search_foods

    items = await search_foods(session, viewer, feed="popular", limit=30)
    scored: list[tuple[Food, FoodEvaluation, float | None, int]] = []

    for item in items:
        ev = await get_food_evaluation(session, item.food.id)
        if ev is None:
            continue
        bonus = 0
        if item.distance_m is not None and item.distance_m < 1500:
            bonus += 15
        elif item.distance_m is not None and item.distance_m < 5000:
            bonus += 8
        final = min(100, ev.overall_score + bonus)
        scored.append((item.food, ev, item.distance_m, final))

    scored.sort(key=lambda x: x[3], reverse=True)
    return [(f, e, d) for f, e, d, _ in scored[:limit]]


def is_stale(updated_at: datetime | None, hours: int = 6) -> bool:
    if updated_at is None:
        return True
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return now - updated_at > timedelta(hours=hours)
