"""Поиск и лента: состояние экрана и обучение на результатах."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import favorite_service, food_service, memory_service
from backend.services.food_service import FoodWithDistance
from backend.services.insights_service import activity_counts
from backend.utils.categories import SEP, food_group, normalize_category
from backend.utils.search_intent import parse_search_intent

FeedState = str  # browse | search_results | search_empty | no_supply | no_geo


def _score_food_fast(
    item: FoodWithDistance,
    prefer_groups: list[str],
    weak_groups: set[str] | None = None,
    meal_ctx=None,
    viewer: User | None = None,
    wellness_day=None,
) -> int:
    food = item.food
    cook = food.cook
    base = 42 + min(28, food.orders_count * 2) + int(cook.rating_avg * 8)
    group = food_group(food.category)
    if group in prefer_groups:
        base += 14 - prefer_groups.index(group) * 4
    if weak_groups and group in weak_groups:
        base -= 14
    if meal_ctx is not None:
        from backend.services.meal_context import score_adjustments

        base += score_adjustments(
            ctx=meal_ctx,
            food_group_name=group,
            food_category=food.category,
            cooking_minutes=food.cooking_time_minutes,
            cook_online=bool(cook.is_online),
        )
    if viewer and viewer.wellness_consent and meal_ctx is not None and wellness_day is not None:
        from backend.services.nutrition_service import wellness_score_for_food

        base += wellness_score_for_food(
            food, user=viewer, day=wellness_day, meal_ctx=meal_ctx,
        )
    if item.distance_m is not None:
        if item.distance_m < 800:
            base += 16
        elif item.distance_m < 2000:
            base += 10
        elif item.distance_m < 5000:
            base += 4
    return min(100, max(0, base))


def _pick_top(
    items: list[FoodWithDistance],
    scores: dict[int, int],
) -> FoodWithDistance | None:
    if not items:
        return None
    return min(items, key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")))


def _feed_state(
    *,
    query: str,
    has_location: bool,
    food_count: int,
    cook_count: int,
) -> FeedState:
    total = food_count + cook_count
    if query.strip():
        return "search_empty" if total == 0 else "search_results"
    if not has_location and total == 0:
        return "no_geo"
    if total == 0:
        return "no_supply"
    return "browse"


def _group_foods(
    items: list[FoodWithDistance],
    *,
    has_location: bool,
    cat_hint: dict | None,
    scores: dict[int, int],
    top_id: int | None = None,
) -> list[dict]:
    if not items:
        return []

    rest = [i for i in items if top_id is None or i.food.id != top_id]
    groups: list[dict] = []

    if top_id is not None:
        top_item = next((i for i in items if i.food.id == top_id), None)
        if top_item:
            groups.append({
                "title": "Выбор",
                "subtitle": None,
                "kind": "foods",
                "items": [top_item],
            })

    if has_location and any(i.distance_m is not None for i in rest):
        bands: list[tuple[str, str | None, float, float]] = [
            ("До 800 м", None, 0, 800),
            ("До 2 км", None, 800, 2000),
            ("До 5 км", None, 2000, 5000),
            ("Дальше", None, 5000, float("inf")),
        ]
        for title, sub, lo, hi in bands:
            bucket = [i for i in rest if i.distance_m is not None and lo <= i.distance_m < hi]
            bucket.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or 0))
            if bucket:
                groups.append({"title": title, "subtitle": sub, "kind": "foods", "items": bucket})
        unknown = [i for i in rest if i.distance_m is None]
        if unknown:
            unknown.sort(key=lambda i: -scores.get(i.food.id, 0))
            groups.append({"title": "Без расстояния", "subtitle": None, "kind": "foods", "items": unknown})
        return groups

    if cat_hint and cat_hint.get("group") != "Разное":
        by_sub: dict[str, list[FoodWithDistance]] = defaultdict(list)
        for item in rest:
            fc = normalize_category(item.food.category)
            leaf = fc.split(SEP)[-1] if SEP in fc else fc
            by_sub[leaf].append(item)
        groups.extend([
            {
                "title": name,
                "subtitle": cat_hint["group"],
                "kind": "foods",
                "items": sorted(bucket, key=lambda i: (-scores.get(i.food.id, 0), i.food.price)),
            }
            for name, bucket in sorted(by_sub.items(), key=lambda x: x[0].lower())
        ])
        return groups

    by_group: dict[str, list[FoodWithDistance]] = defaultdict(list)
    for item in rest:
        fc = normalize_category(item.food.category)
        g = fc.split(SEP)[0] if SEP in fc else fc
        by_group[g].append(item)
    groups.extend([
        {
            "title": name,
            "subtitle": None,
            "kind": "foods",
            "items": sorted(bucket, key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf"))),
        }
        for name, bucket in sorted(by_group.items(), key=lambda x: x[0].lower())
    ])
    return groups


def _group_cooks(cooks: list[tuple[User, float | None]]) -> list[dict]:
    if not cooks:
        return []
    bands: list[tuple[str, str | None, float, float]] = [
        ("До 1 км", None, 0, 1000),
        ("До 3 км", None, 1000, 3000),
        ("Дальше", None, 3000, float("inf")),
    ]
    groups: list[dict] = []
    for title, sub, lo, hi in bands:
        bucket = [(c, d) for c, d in cooks if d is not None and lo <= d < hi]
        bucket.sort(key=lambda x: (-x[0].rating_avg, -x[0].rating_count))
        if bucket:
            groups.append({"title": title, "subtitle": sub, "kind": "cooks", "cook_items": bucket})
    no_dist = [(c, d) for c, d in cooks if d is None]
    if no_dist:
        groups.append({"title": "Повара", "subtitle": None, "kind": "cooks", "cook_items": no_dist})
    return groups


async def assistant_search(
    session: AsyncSession,
    viewer: User,
    query: str = "",
    *,
    scope: str = "feed",
) -> dict:
    has_location = viewer.lat is not None and viewer.lon is not None
    intent = parse_search_intent(query, has_location=has_location)
    intent = await memory_service.enrich_intent(session, viewer, intent)

    weak = set(intent.get("weak_groups") or [])
    meal_ctx = intent.get("meal_context")
    prefer_groups = await memory_service.preferred_groups(session, viewer.id)
    wellness_day = None
    if viewer.wellness_consent:
        from backend.services.wellness_tracker import get_day_nutrition

        _, wellness_day = await get_day_nutrition(session, viewer)
    if intent.get("prefer_groups_memory"):
        prefer_groups = intent["prefer_groups_memory"] + [
            g for g in prefer_groups if g not in intent["prefer_groups_memory"]
        ]

    suggestions = await memory_service.quick_suggestions(session, viewer)

    include_foods = scope in ("feed", "all")
    include_cooks = scope in ("cooks", "all") or intent["wants_cooks"]

    food_items: list[FoodWithDistance] = []
    cook_items: list[tuple[User, float | None]] = []
    limit = 50
    search_q = intent.get("db_query") or intent["query"] or None

    if include_foods:
        food_items = await food_service.search_foods(
            session,
            viewer,
            feed=intent["feed"],
            category=intent["category"] if search_q or intent.get("vague") else None,
            q=search_q,
            max_distance_m=intent["max_distance_m"],
            price_max=intent["price_max"],
            min_rating=intent["min_rating"],
            exclude_groups=intent.get("exclude_groups"),
            strict_category=intent.get("strict_category", False),
            limit=limit,
        )
        if search_q and not food_items and intent.get("strict_category"):
            food_items = await food_service.search_foods(
                session,
                viewer,
                feed=intent["feed"],
                category=intent["category"],
                q=None,
                max_distance_m=intent["max_distance_m"],
                price_max=intent["price_max"],
                min_rating=intent["min_rating"],
                exclude_groups=intent.get("exclude_groups"),
                strict_category=True,
                limit=limit,
            )
        if search_q and not food_items and not intent.get("strict_category"):
            food_items = await food_service.search_foods(
                session,
                viewer,
                feed=intent["feed"],
                q=search_q,
                max_distance_m=None,
                price_max=intent["price_max"],
                min_rating=intent["min_rating"],
                limit=limit,
            )
        if not search_q:
            from backend.services import nutrition_service

            recs_raw = await nutrition_service.harmonious_recommendations(
                session, viewer, limit=12, prefer_groups=prefer_groups,
            )
            seen = {i.food.id for i in food_items}
            for food, _ev, dist in recs_raw:
                if food.id not in seen:
                    food_items.insert(0, FoodWithDistance(food=food, distance_m=dist))
                    seen.add(food.id)

    if viewer.diet_preference:
        from backend.services.nutrition_service import food_matches_diet

        food_items = [
            i
            for i in food_items
            if food_matches_diet(i.food.name, i.food.category, viewer.diet_preference)
        ]

    if include_cooks:
        cook_items = await food_service.search_cooks(
            session,
            viewer,
            q=search_q,
            max_distance_m=intent["max_distance_m"],
            min_rating=intent["min_rating"],
            limit=30,
        )

    scores = {
        item.food.id: _score_food_fast(
            item, prefer_groups, weak, meal_ctx, viewer, wellness_day,
        )
        for item in food_items
    }

    if intent["feed"] == "cheap":
        food_items.sort(key=lambda i: (i.food.price, i.distance_m or float("inf")))
    else:
        food_items.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")))

    top_item = _pick_top(food_items, scores) if include_foods else None
    top_id = top_item.food.id if top_item else None

    groups: list[dict] = []
    if include_foods and food_items:
        groups.extend(
            _group_foods(
                food_items,
                has_location=has_location,
                cat_hint=intent["category_hint"],
                scores=scores,
                top_id=top_id if len(food_items) > 1 else None,
            )
        )
    if include_cooks and cook_items:
        groups.extend(_group_cooks(cook_items))

    fav_foods = await favorite_service.get_favorite_food_ids(session, viewer)
    fav_cooks = await favorite_service.get_favorite_cook_ids(session, viewer)

    state = _feed_state(
        query=query,
        has_location=has_location,
        food_count=len(food_items),
        cook_count=len(cook_items),
    )

    action: str | None = None
    if state == "search_empty":
        action = "create_wish"

    if query.strip():
        await memory_service.observe_search(
            session,
            viewer,
            query.strip(),
            category_hint=intent["category_hint"],
            results_count=len(food_items) + len(cook_items),
            price_max=intent.get("price_max"),
        )
        await session.commit()

    activity = await activity_counts(session, viewer) if scope == "feed" else None

    from backend.services.meal_context import context_payload

    ctx_out = context_payload(meal_ctx) if meal_ctx else None
    if viewer.wellness_consent and scope == "feed":
        from backend.services.nutrition_service import feed_wellness_context

        wellness_ctx = await feed_wellness_context(session, viewer)
        if ctx_out and wellness_ctx:
            ctx_out = {**ctx_out, **wellness_ctx}

    return {
        "state": state,
        "has_location": has_location,
        "activity": activity,
        "context": ctx_out,
        "message": "",
        "companion": "",
        "suggestions": suggestions,
        "action": action,
        "top_pick": {
            "food_id": top_item.food.id,
            "label": top_item.food.name,
        } if top_item else None,
        "intent": {
            "category": intent["category_hint"]["label"],
            "feed": intent["feed"],
            "max_distance_m": intent["max_distance_m"],
            "price_max": intent["price_max"],
        },
        "groups": groups,
        "favorite_food_ids": fav_foods,
        "favorite_cook_ids": fav_cooks,
        "total_foods": len(food_items),
        "total_cooks": len(cook_items),
    }
