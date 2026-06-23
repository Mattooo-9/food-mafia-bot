"""Умный поиск: один запрос — ИИ сам структурирует, группирует и сортирует."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import ai_analyst_service, favorite_service, food_service
from backend.services.food_service import FoodWithDistance
from backend.utils.categories import SEP, normalize_category
from backend.utils.search_intent import parse_search_intent


def _dist_label(m: float | None) -> str:
    if m is None:
        return ""
    if m < 1000:
        return f"{int(m)} м"
    return f"{m / 1000:.1f} км"


def _build_message(intent: dict, food_count: int, cook_count: int) -> str:
    q = intent["query"]
    if not q:
        if food_count or cook_count:
            return "Подобрал лучшее рядом — напишите, что хотите, и я сам всё уточню."
        return "Напишите, что хотите поесть — я сам разложу по группам и найду ближайшее."

    cat = intent["category_hint"]
    parts: list[str] = []

    if cat["group"] != "Разное":
        parts.append(cat["label"])
    else:
        parts.append(f"«{q}»")

    if intent["price_max"]:
        parts.append(f"до {int(intent['price_max'])} ⭐")
    if intent["sort_labels"]:
        parts.append(", ".join(intent["sort_labels"]))

    total = food_count + cook_count
    if total == 0:
        if cat.get("group") != "Разное" and cat.get("score", 0) >= 1:
            return f"По «{q}» пока нет подходящих блюд рядом — только {cat['label'].lower()}."
        return f"По запросу «{q}» пока пусто — попробуйте проще: «борщ», «салат», «недорого»."

    tail = []
    if food_count:
        tail.append(f"{food_count} блюд")
    if cook_count:
        tail.append(f"{cook_count} поваров")
    return f"{' · '.join(parts)} — {' и '.join(tail)}."


async def _score_food(session: AsyncSession, item: FoodWithDistance) -> int:
    ev = await ai_analyst_service.get_food_evaluation(session, item.food.id)
    base = ev.overall_score if ev else 55
    bonus = 0
    if item.distance_m is not None:
        if item.distance_m < 800:
            bonus += 18
        elif item.distance_m < 2000:
            bonus += 12
        elif item.distance_m < 5000:
            bonus += 6
    return min(100, base + bonus)


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
            ("Рядом с вами", "до 2 км", 800, 2000),
            ("В районе", "до 5 км", 2000, 5000),
            ("Подальше", None, 5000, float("inf")),
        ]
        groups: list[dict] = []
        for title, sub, lo, hi in bands:
            bucket = [
                i
                for i in items
                if i.distance_m is not None and lo <= i.distance_m < hi
            ]
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
        groups = []
        for name in sorted(by_sub.keys(), key=str.lower):
            bucket = by_sub[name]
            bucket.sort(key=lambda i: (-scores.get(i.food.id, 0), i.food.price))
            groups.append({"title": name, "subtitle": cat_hint["group"], "kind": "foods", "items": bucket})
        return groups

    by_group: dict[str, list[FoodWithDistance]] = defaultdict(list)
    for item in items:
        fc = normalize_category(item.food.category)
        g = fc.split(SEP)[0] if SEP in fc else fc
        by_group[g].append(item)
    groups = []
    for name in sorted(by_group.keys(), key=str.lower):
        bucket = by_group[name]
        bucket.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")))
        groups.append({"title": name, "subtitle": None, "kind": "foods", "items": bucket})
    return groups


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

    include_foods = scope in ("feed", "all")
    include_cooks = scope in ("cooks", "all") or intent["wants_cooks"]

    food_items: list[FoodWithDistance] = []
    cook_items: list[tuple[User, float | None]] = []

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
            limit=80,
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
                limit=80,
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
                limit=80,
            )
        if not q:
            from backend.services import nutrition_service

            recs = await nutrition_service.harmonious_recommendations(session, viewer, limit=12)
            if not recs:
                recs_raw = await ai_analyst_service.get_recommendations(session, viewer, limit=12)
                recs = recs_raw
            else:
                recs_raw = recs
            seen = {i.food.id for i in food_items}
            for item in recs_raw:
                if isinstance(item, tuple) and len(item) == 3:
                    food, _ev, dist = item
                else:
                    continue
                if food.id not in seen:
                    food_items.insert(0, FoodWithDistance(food=food, distance_m=dist))
                    seen.add(food.id)

    if include_cooks:
        cook_items = await food_service.search_cooks(
            session,
            viewer,
            q=intent["query"] or None,
            max_distance_m=intent["max_distance_m"],
            min_rating=intent["min_rating"],
            limit=40,
        )

    scores: dict[int, int] = {}
    for item in food_items:
        scores[item.food.id] = await _score_food(session, item)

    if intent["feed"] == "cheap":
        food_items.sort(key=lambda i: (i.food.price, i.distance_m or float("inf")))
    elif scores:
        food_items.sort(
            key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")),
        )

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

    wellness_note = ""
    if viewer.wellness_consent:
        from backend.services import nutrition_service

        tip = await nutrition_service.wellness_tip(session, viewer)
        if tip.get("message"):
            wellness_note = tip["message"]

    msg = _build_message(intent, len(food_items), len(cook_items))
    if wellness_note and not query.strip():
        msg = f"{wellness_note} {msg}"

    return {
        "message": msg,
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
