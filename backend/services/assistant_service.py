"""Умный поиск: быстро, кратко, с памятью о пользователе."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import favorite_service, food_service, memory_service
from backend.services.food_service import FoodWithDistance
from backend.services.nutrition_service import balance_hint_for_intent, food_matches_diet, wellness_tip
from backend.utils.categories import SEP, food_group, normalize_category
from backend.utils.search_intent import parse_search_intent


def _score_food_fast(item: FoodWithDistance, prefer_groups: list[str]) -> int:
    food = item.food
    cook = food.cook
    base = 42 + min(28, food.orders_count * 2) + int(cook.rating_avg * 8)
    group = food_group(food.category)
    if group in prefer_groups:
        base += 14 - prefer_groups.index(group) * 4
    if item.distance_m is not None:
        if item.distance_m < 800:
            base += 16
        elif item.distance_m < 2000:
            base += 10
        elif item.distance_m < 5000:
            base += 4
    return min(100, base)


def _build_message(
    intent: dict,
    food_count: int,
    cook_count: int,
    *,
    wellness: str = "",
    companion: str = "",
) -> str:
    q = intent["query"]
    prefix = ""
    if companion and len(companion) < 80:
        prefix = f"{companion}. "

    if not q:
        core = wellness or "Подобрал рядом."
        if food_count or cook_count:
            return f"{prefix}{core}"
        return prefix + (wellness or "Напишите, что хотите — подберу быстро.")

    cat = intent["category_hint"]
    label = cat["label"] if cat["group"] != "Разное" else f"«{q}»"
    total = food_count + cook_count

    if total == 0:
        if cat.get("score", 0) >= 1:
            return f"{prefix}«{q}» — пусто. Опубликуйте запрос в «Заказах»."
        return f"{prefix}«{q}» — не нашёл. Короче или запрос поварам."

    bits = [label]
    if intent["price_max"]:
        bits.append(f"до {int(intent['price_max'])}⭐")
    tail = f"{food_count} блюд" if cook_count == 0 else f"{food_count} блюд, {cook_count} поваров"
    return f"{prefix}{' · '.join(bits)} — {tail}."


def _group_foods(
    items: list[FoodWithDistance],
    *,
    has_location: bool,
    cat_hint: dict | None,
    scores: dict[int, int],
) -> list[dict]:
    if not items:
        return []

    if has_location and any(i.distance_m is not None for i in items):
        bands: list[tuple[str, str | None, float, float]] = [
            ("Совсем рядом", "до 800 м", 0, 800),
            ("Рядом", "до 2 км", 800, 2000),
            ("В районе", "до 5 км", 2000, 5000),
            ("Подальше", None, 5000, float("inf")),
        ]
        groups: list[dict] = []
        for title, sub, lo, hi in bands:
            bucket = [i for i in items if i.distance_m is not None and lo <= i.distance_m < hi]
            bucket.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or 0))
            if bucket:
                groups.append({"title": title, "subtitle": sub, "kind": "foods", "items": bucket})
        unknown = [i for i in items if i.distance_m is None]
        if unknown:
            unknown.sort(key=lambda i: -scores.get(i.food.id, 0))
            groups.append({"title": "Без координат", "subtitle": None, "kind": "foods", "items": unknown})
        return groups

    if cat_hint and cat_hint.get("group") != "Разное":
        by_sub: dict[str, list[FoodWithDistance]] = defaultdict(list)
        for item in items:
            fc = normalize_category(item.food.category)
            leaf = fc.split(SEP)[-1] if SEP in fc else fc
            by_sub[leaf].append(item)
        return [
            {
                "title": name,
                "subtitle": cat_hint["group"],
                "kind": "foods",
                "items": sorted(bucket, key=lambda i: (-scores.get(i.food.id, 0), i.food.price)),
            }
            for name, bucket in sorted(by_sub.items(), key=lambda x: x[0].lower())
        ]

    by_group: dict[str, list[FoodWithDistance]] = defaultdict(list)
    for item in items:
        fc = normalize_category(item.food.category)
        g = fc.split(SEP)[0] if SEP in fc else fc
        by_group[g].append(item)
    return [
        {
            "title": name,
            "subtitle": None,
            "kind": "foods",
            "items": sorted(bucket, key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf"))),
        }
        for name, bucket in sorted(by_group.items(), key=lambda x: x[0].lower())
    ]


def _group_cooks(cooks: list[tuple[User, float | None]]) -> list[dict]:
    if not cooks:
        return []
    bands: list[tuple[str, str | None, float, float]] = [
        ("Повара рядом", "до 1 км", 0, 1000),
        ("Недалеко", "до 3 км", 1000, 3000),
        ("В городе", None, 3000, float("inf")),
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
    prefer_groups = await memory_service.preferred_groups(session, viewer.id)
    companion = await memory_service.companion_line(session, viewer)

    include_foods = scope in ("feed", "all")
    include_cooks = scope in ("cooks", "all") or intent["wants_cooks"]

    food_items: list[FoodWithDistance] = []
    cook_items: list[tuple[User, float | None]] = []
    limit = 50

    if include_foods:
        q = intent["query"] or None
        food_items = await food_service.search_foods(
            session,
            viewer,
            feed=intent["feed"],
            category=intent["category"] if q else None,
            q=q,
            max_distance_m=intent["max_distance_m"],
            price_max=intent["price_max"],
            min_rating=intent["min_rating"],
            exclude_groups=intent.get("exclude_groups"),
            strict_category=intent.get("strict_category", False),
            limit=limit,
        )
        if q and not food_items and intent.get("strict_category"):
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
        if q and not food_items and not intent.get("strict_category"):
            food_items = await food_service.search_foods(
                session,
                viewer,
                feed=intent["feed"],
                q=q,
                max_distance_m=None,
                price_max=intent["price_max"],
                min_rating=intent["min_rating"],
                limit=limit,
            )
        if not q:
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
        food_items = [
            i
            for i in food_items
            if food_matches_diet(i.food.name, i.food.category, viewer.diet_preference)
        ]

    if include_cooks:
        cook_items = await food_service.search_cooks(
            session,
            viewer,
            q=intent["query"] or None,
            max_distance_m=intent["max_distance_m"],
            min_rating=intent["min_rating"],
            limit=30,
        )

    scores = {item.food.id: _score_food_fast(item, prefer_groups) for item in food_items}

    if intent["feed"] == "cheap":
        food_items.sort(key=lambda i: (i.food.price, i.distance_m or float("inf")))
    else:
        food_items.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")))

    groups: list[dict] = []
    if include_foods and food_items:
        groups.extend(
            _group_foods(
                food_items,
                has_location=has_location,
                cat_hint=intent["category_hint"],
                scores=scores,
            )
        )
    if include_cooks and cook_items:
        groups.extend(_group_cooks(cook_items))

    fav_foods = await favorite_service.get_favorite_food_ids(session, viewer)
    fav_cooks = await favorite_service.get_favorite_cook_ids(session, viewer)

    tip = await wellness_tip(session, viewer)
    wellness_note = tip.get("message", "")
    if query.strip() and intent.get("strict_category"):
        hint = balance_hint_for_intent(intent["category_hint"])
        if hint and len(hint) < 90:
            wellness_note = hint

    msg = _build_message(
        intent,
        len(food_items),
        len(cook_items),
        wellness=wellness_note if not query.strip() else "",
        companion=companion if not query.strip() else "",
    )

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

    return {
        "message": msg[:320],
        "companion": companion[:120],
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
