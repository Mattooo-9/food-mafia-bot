from fastapi import APIRouter, HTTPException, Query

from backend.api.deps import CurrentUser, SessionDep
from backend.api.serializers import serialize_cook, serialize_food
from backend.api.schemas import (
    AssistantGroupOut,
    AssistantIntentOut,
    AssistantSearchOut,
    CategorizeOut,
    FoodEvaluationOut,
    MarketInsightOut,
    MarketOverviewOut,
    PriceSuggestionOut,
    RecommendationOut,
)
from backend.services import ai_analyst_service, analytics_service, assistant_service, food_service, search_history_service
from backend.services.analytics_service import region_key
from backend.utils.categories import categorize_text
from backend.services.food_service import FoodError

router = APIRouter(tags=["ai"])


@router.get("/ai/categorize", response_model=CategorizeOut)
async def ai_categorize(
    user: CurrentUser,
    name: str = Query(default=""),
    description: str = Query(default=""),
    q: str = Query(default=""),
) -> CategorizeOut:
    return CategorizeOut(**categorize_text(name=name, description=description, query=q))


@router.get("/ai/search", response_model=AssistantSearchOut)
async def ai_search(
    user: CurrentUser,
    session: SessionDep,
    q: str = Query(default="", max_length=256),
    scope: str = Query(default="feed", pattern="^(feed|cooks|all)$"),
) -> AssistantSearchOut:
    data = await assistant_service.assistant_search(session, user, q, scope=scope)
    fav_f = data["favorite_food_ids"]
    fav_c = data["favorite_cook_ids"]
    groups_out: list[AssistantGroupOut] = []
    for g in data["groups"]:
        foods = []
        cooks = []
        if g["kind"] == "foods":
            for item in g["items"]:
                foods.append(serialize_food(item.food, item.distance_m, fav_f))
        else:
            for cook, dist in g["cook_items"]:
                cooks.append(serialize_cook(cook, dist, fav_c))
        groups_out.append(
            AssistantGroupOut(
                title=g["title"],
                subtitle=g.get("subtitle"),
                kind=g["kind"],
                foods=foods,
                cooks=cooks,
            )
        )
    intent = data["intent"]
    total = data["total_foods"] + data["total_cooks"]
    if q.strip():
        await search_history_service.record_search(
            session,
            user.id,
            q.strip(),
            scope=scope,
            results_count=total,
            summary=data["message"],
        )
    return AssistantSearchOut(
        message=data["message"],
        companion=data.get("companion", ""),
        intent=AssistantIntentOut(
            category=intent["category"],
            feed=intent["feed"],
            max_distance_m=intent["max_distance_m"],
            price_max=intent["price_max"],
        ),
        groups=groups_out,
        total_foods=data["total_foods"],
        total_cooks=data["total_cooks"],
    )


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
        analyst_note="ИИ сам следит за ценами рядом и подсказывает выгодные блюда.",
    )


@router.get("/ai/price-suggestion", response_model=PriceSuggestionOut)
async def price_suggestion(
    category: str,
    user: CurrentUser,
    session: SessionDep,
    price: float | None = Query(default=None, ge=0),
    ingredients: str = Query(default=""),
    description: str = Query(default=""),
    portions: int = Query(default=1, ge=1, le=100),
    cooking_time_minutes: int | None = Query(default=None, ge=1, le=1440),
    name: str = Query(default=""),
) -> PriceSuggestionOut:
    data = await ai_analyst_service.get_price_suggestion(
        session,
        category,
        lat=user.lat,
        lon=user.lon,
        current_price=price,
        ingredients=ingredients,
        description=description,
        portions=portions,
        cooking_time_minutes=cooking_time_minutes,
        dish_name=name,
    )
    return PriceSuggestionOut(**data)


@router.get("/ai/food/{food_id}/evaluation", response_model=FoodEvaluationOut)
async def food_evaluation(food_id: int, user: CurrentUser, session: SessionDep) -> FoodEvaluationOut:
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
        simple_tip=ev.buyer_tip,
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
