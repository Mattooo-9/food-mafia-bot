"""Умный поиск: ИИ сам решает, отвечает коротко и конкретно."""

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


def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    n1 = n % 10
    if 11 <= n <= 19:
        return many
    if n1 == 1:
        return one
    if 2 <= n1 <= 4:
        return few
    return many


def _dist_suffix(m: float | None) -> str:
    if m is None:
        return ""
    if m < 1000:
        return f", {int(m)} м"
    return f", {m / 1000:.1f} км"


def _pick_top(
    items: list[FoodWithDistance],
    scores: dict[int, int],
) -> FoodWithDistance | None:
    if not items:
        return None
    return min(items, key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or float("inf")))


def _top_pick_label(item: FoodWithDistance) -> str:
    f = item.food
    cook = f.cook.cook_name or f.cook.first_name or "повар"
    return f"{f.name} · {int(f.price)}⭐{_dist_suffix(item.distance_m)} · {cook}"


def _build_message(
    intent: dict,
    food_count: int,
    cook_count: int,
    *,
    top: FoodWithDistance | None = None,
    wellness: str = "",
    companion: str = "",
) -> str:
    q = intent["query"]
    cat = intent["category_hint"]
    label = cat["label"] if cat.get("group") != "Разное" else ""
    sort_txt = (intent.get("sort_labels") or [None])[0]
    top_line = f" → {_top_pick_label(top)}" if top else ""

    if not q.strip():
        if food_count:
            base = f"Подобрал {food_count} {_plural(food_count, 'вариант', 'варианта', 'вариантов')}"
            if sort_txt:
                base += f" · {sort_txt}"
            if companion:
                base = f"{companion}. {base}"
            return (base + top_line + ".")[:280]
        return (companion + ". " if companion else "") + (wellness or "Напишите, что хотите — подберу сам.")[:280]

    subject = label or f"«{q}»"
    total = food_count + cook_count

    if total == 0:
        tail = " Опубликуйте запрос — повара приготовят."
        return f"{subject} рядом нет.{tail}"[:280]

    if food_count and not cook_count:
        core = f"{subject}: {food_count} {_plural(food_count, 'блюдо', 'блюда', 'блюд')}"
    elif cook_count and not food_count:
        core = f"{subject}: {cook_count} {_plural(cook_count, 'повар', 'повара', 'поваров')}"
    else:
        core = f"{subject}: {food_count} блюд, {cook_count} поваров"

    extras: list[str] = []
    if intent.get("price_max"):
        extras.append(f"до {int(intent['price_max'])}⭐")
    if sort_txt:
        extras.append(sort_txt)
    if extras:
        core += f" ({', '.join(extras)})"

    return (core + top_line + ".")[:280]


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
                "title": "Рекомендую",
                "subtitle": "лучший вариант",
                "kind": "foods",
                "items": [top_item],
            })

    if has_location and any(i.distance_m is not None for i in rest):
        bands: list[tuple[str, str | None, float, float]] = [
            ("Совсем рядом", "до 800 м", 0, 800),
            ("Рядом", "до 2 км", 800, 2000),
            ("В районе", "до 5 км", 2000, 5000),
            ("Подальше", None, 5000, float("inf")),
        ]
        for title, sub, lo, hi in bands:
            bucket = [i for i in rest if i.distance_m is not None and lo <= i.distance_m < hi]
            bucket.sort(key=lambda i: (-scores.get(i.food.id, 0), i.distance_m or 0))
            if bucket:
                groups.append({"title": title, "subtitle": sub, "kind": "foods", "items": bucket})
        unknown = [i for i in rest if i.distance_m is None]
        if unknown:
            unknown.sort(key=lambda i: -scores.get(i.food.id, 0))
            groups.append({"title": "Без координат", "subtitle": None, "kind": "foods", "items": unknown})
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
    intent = await memory_service.enrich_intent(session, viewer, intent)

    prefer_groups = await memory_service.preferred_groups(session, viewer.id)
    if intent.get("prefer_groups_memory"):
        prefer_groups = intent["prefer_groups_memory"] + [g for g in prefer_groups if g not in intent["prefer_groups_memory"]]

    companion = await memory_service.companion_line(session, viewer)
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

    scores = {item.food.id: _score_food_fast(item, prefer_groups) for item in food_items}

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

    tip = await wellness_tip(session, viewer)
    wellness_note = tip.get("message", "")
    if query.strip() and intent.get("strict_category"):
        hint = balance_hint_for_intent(intent["category_hint"])
        if hint and len(hint) < 70:
            wellness_note = hint

    msg = _build_message(
        intent,
        len(food_items),
        len(cook_items),
        top=top_item if query.strip() or top_item else top_item,
        wellness=wellness_note if not query.strip() else "",
        companion=companion if not query.strip() else "",
    )

    action: str | None = None
    if query.strip() and len(food_items) + len(cook_items) == 0:
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

    return {
        "message": msg,
        "companion": companion[:120],
        "suggestions": suggestions,
        "action": action,
        "top_pick": {
            "food_id": top_item.food.id,
            "label": _top_pick_label(top_item),
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
