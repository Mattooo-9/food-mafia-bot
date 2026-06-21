from fastapi import APIRouter, HTTPException, Query

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import (
    FoodEvaluationOut,
    MarketInsightOut,
    MarketOverviewOut,
    PriceSuggestionOut,
    RecommendationOut,
)
from backend.services import ai_analyst_service, analytics_service, food_service
from backend.services.analytics_service import region_key
from backend.services.food_service import FoodError

router = APIRouter(tags=["ai"])


@router.get("/ai/market", response_model=MarketOverviewOut)
async def get_market_overview(user: CurrentUser, session: SessionDep) -> MarketOverviewOut:
    overview = await analytics_service.get_market_overview(
        session,
        lat=user.lat,
        lon=user.lon,
    )
    cached = await ai_analyst_service.get_cached_market(
        session, region_key=region_key(user.lat, user.lon)
    )
    if not cached:
        cached = await ai_analyst_service.get_cached_market(session, region_key="global")
    insights = [
        MarketInsightOut(
            category=s.category,
            dish_count=s.dish_count,
            median_price=s.median_price,
            avg_price=s.avg_price,
            min_price=s.min_price,
            max_price=s.max_price,
            avg_rating=s.avg_rating,
            demand_index=s.demand_index,
            competition_index=s.competition_index,
            trend=s.trend,
            trend_label=ai_analyst_service.TREND_LABELS.get(s.trend, s.trend),
            summary=s.summary,
        )
        for s in cached
    ]
    if not insights and overview.categories:
        for cat in overview.categories:
            demand = analytics_service.demand_index(cat)
            insights.append(
                MarketInsightOut(
                    category=cat.category,
                    dish_count=cat.dish_count,
                    median_price=cat.median_price,
                    avg_price=cat.avg_price,
                    min_price=cat.min_price,
                    max_price=cat.max_price,
                    avg_rating=cat.avg_rating,
                    demand_index=demand,
                    competition_index=analytics_service.competition_index(cat.dish_count),
                    trend="stable",
                    trend_label="Стабильный рынок",
                    summary=f"«{cat.category}»: медиана {int(cat.median_price)} ⭐, {cat.dish_count} блюд.",
                )
            )

    return MarketOverviewOut(
        total_dishes=overview.total_dishes,
        total_orders=overview.total_orders,
        avg_price=overview.avg_price,
        median_price=overview.median_price,
        avg_rating=overview.avg_rating,
        top_category=overview.top_category,
        insights=insights,
        analyst_note=(
            "ИИ учитывает реальные цены в вашем районе, сезон и расходники — "
            "чтобы было выгодно и повару, и покупателю."
        ),
    )


@router.get("/ai/price-suggestion", response_model=PriceSuggestionOut)
async def price_suggestion(
    category: str,
    user: CurrentUser,
    session: SessionDep,
    price: float | None = Query(default=None, ge=0),
    ingredients: str = Query(default=""),
    portions: int = Query(default=1, ge=1, le=100),
    cooking_time_minutes: int = Query(default=30, ge=1, le=1440),
    name: str = Query(default=""),
) -> PriceSuggestionOut:
    data = await ai_analyst_service.get_price_suggestion(
        session,
        category,
        lat=user.lat,
        lon=user.lon,
        current_price=price,
        ingredients=ingredients,
        portions=portions,
        cooking_time_minutes=cooking_time_minutes,
        dish_name=name,
    )
    return PriceSuggestionOut(**data)


@router.get("/ai/food/{food_id}/evaluation", response_model=FoodEvaluationOut)
async def food_evaluation(food_id: int, session: SessionDep) -> FoodEvaluationOut:
    ev = await ai_analyst_service.get_food_evaluation(session, food_id)
    if ev is None:
        food = await food_service.get_food(session, food_id)
        if food is None:
            raise HTTPException(status_code=404, detail="Блюдо не найдено")
        overview = await analytics_service.get_market_overview(session)
        stats_by_cat = {c.category: c for c in overview.categories}
        ev = await ai_analyst_service.evaluate_food(session, food, food.cook, stats_by_cat)
        await session.commit()
    return FoodEvaluationOut(
        food_id=ev.food_id,
        price_score=ev.price_score,
        quality_score=ev.quality_score,
        demand_score=ev.demand_score,
        overall_score=ev.overall_score,
        verdict=ev.verdict,
        verdict_label=ai_analyst_service.VERDICT_LABELS.get(ev.verdict, ev.verdict),
        fair_price=ev.fair_price,
        suggested_price_min=ev.suggested_price_min,
        suggested_price_max=ev.suggested_price_max,
        summary=ev.summary,
        buyer_tip=ev.buyer_tip,
    )


@router.get("/ai/recommendations", response_model=list[RecommendationOut])
async def recommendations(user: CurrentUser, session: SessionDep) -> list[RecommendationOut]:
    try:
        recs = await ai_analyst_service.get_recommendations(session, user, limit=8)
    except FoodError:
        recs = []
    return [
        RecommendationOut(
            food_id=food.id,
            food_name=food.name,
            food_photo=food.photo,
            price=food.price,
            cook_name=food.cook.cook_name or food.cook.first_name,
            distance_m=round(dist, 1) if dist is not None else None,
            overall_score=ev.overall_score,
            buyer_tip=ev.buyer_tip,
            verdict_label=ai_analyst_service.VERDICT_LABELS.get(ev.verdict, ev.verdict),
        )
        for food, ev, dist in recs
    ]


@router.post("/ai/refresh")
async def refresh_ai_data(user: CurrentUser, session: SessionDep) -> dict:
    if not user.is_cook:
        raise HTTPException(status_code=403, detail="Только для поваров")
    count = await ai_analyst_service.refresh_market_data(session)
    return {"ok": True, "evaluations_updated": count}
