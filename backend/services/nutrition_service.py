"""Гармоничные рекомендации: калории, радуга, вода, режим приёмов пищи."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import ai_analyst_service, food_service
from backend.services.meal_context import build_meal_context, hour_bucket, local_now
from backend.services.nutrient_engine import (
    RAINBOW_ORDER,
    daily_calorie_target,
    estimate_food_nutrients,
    harmony_hint,
    meal_calorie_budget,
    meal_schedule_hint,
    missing_rainbow_colors,
    rainbow_progress,
    score_food_for_wellness,
    water_reminder_text,
)
from backend.services.wellness_tracker import get_day_nutrition
from backend.utils.categories import SEP, categorize_text, food_group, normalize_category

_BALANCE_HINTS: dict[str, str] = {
    "Горячие блюда": "К горячему — салат или тёплый напиток.",
    "Выпечка и сладкое": "Сладкое в умеренной порции; дополните супом или чаем.",
    "Закуски и салаты": "К салату — сытное горячее или цельный хлеб.",
    "На каждый день": "Чередуйте лёгкие и сытные приёмы — баланс энергии.",
}

_LIGHT_GROUPS = {"Закуски и салаты", "На каждый день"}
_HEAVY_GROUPS = {"Горячие блюда", "Выпечка и сладкое"}

_MEAT_MARKERS = ("мяс", "свинин", "говядин", "баран", "котлет", "фарш", "бекон")
_SWEET_MARKERS = ("слад", "торт", "десерт", "шоколад", "печень")

_RECIPE_IDEAS: dict[str, list[str]] = {
    "Супы": [
        "Домашний борщ на говядине с запечёнными овощами",
        "Крем-суп из тыквы с имбирём на овощном бульоне",
        "Лёгкий куриный бульон с зеленью",
    ],
    "Салаты": [
        "Салат из сезонных овощей с оливковым маслом",
        "Винегрет с капустой — просто и полезно",
    ],
    "Основные": [
        "Запечённая рыба с лимоном и травами",
        "Тушёные овощи с крупой",
    ],
    "Выпечка": [
        "Цельнозерновой хлеб на закваске",
        "Овсяные оладьи с ягодами",
    ],
}

_ACTIVITY_LABELS = {
    "sedentary": "мало движения",
    "light": "лёгкая активность",
    "moderate": "умеренная",
    "active": "активный спорт",
    "intense": "интенсивные тренировки",
}


def _hour_bucket(user: User | None = None) -> str:
    if user is None:
        return hour_bucket()
    return build_meal_context(user=user).bucket


async def _recent_search_groups(session: AsyncSession, user_id: int) -> list[str]:
    from backend.models import SearchHistory

    result = await session.execute(
        select(SearchHistory.query)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(8)
    )
    groups: list[str] = []
    for (q,) in result.all():
        cat = categorize_text(query=q or "")
        if cat["group"] != "Разное":
            groups.append(cat["group"])
    return groups


def food_matches_diet(food_name: str, food_category: str, diet: str | None) -> bool:
    if not diet:
        return True
    d = diet.lower()
    blob = f"{food_name} {food_category}".lower()
    if any(m in d for m in ("без мяс", "веган", "пост")):
        if food_group(food_category) == "Горячие блюда" and "Мясные" in food_category:
            return False
        if any(m in blob for m in _MEAT_MARKERS):
            return False
    if "без слад" in d or "мало сахар" in d:
        if food_group(food_category) == "Выпечка и сладкое":
            if "Десерт" in food_category or any(m in blob for m in _SWEET_MARKERS):
                return False
    if "легк" in d or "лёгк" in d:
        if food_group(food_category) in _HEAVY_GROUPS and "Десерт" in food_category:
            return False
    return True


async def build_wellness_snapshot(session: AsyncSession, user: User) -> dict:
    now = local_now(user)
    ctx = build_meal_context(user=user)
    _, day = await get_day_nutrition(session, user)

    daily_target = daily_calorie_target(user.activity_level)
    meal_budget = meal_calorie_budget(ctx.bucket, user.activity_level)
    kcal_left = max(0, daily_target - day.kcal_total)
    meal_left = max(0, meal_budget - sum(m.get("kcal", 0) for m in day.meals if m.get("bucket") == ctx.bucket))

    last_water_hour: int | None = None
    if day.last_water_at:
        try:
            from datetime import datetime

            last_water_hour = datetime.fromisoformat(day.last_water_at).hour
        except ValueError:
            last_water_hour = None

    water = water_reminder_text(now.hour, day.water_glasses, last_water_hour)
    schedule = meal_schedule_hint(ctx.bucket, now.hour)
    harmony = harmony_hint(day, ctx.bucket, ctx.prefer_groups[0] if ctx.prefer_groups else None)
    missing = missing_rainbow_colors(day)

    message = ctx.section_label
    if user.wellness_consent:
        recent = await _recent_search_groups(session, user.id)
        if recent:
            last = recent[0]
            if last in _HEAVY_GROUPS and ctx.bucket in ("evening", "night"):
                message = "После сытного — суп или салат"
            elif last in _LIGHT_GROUPS and ctx.bucket == "lunch":
                message = "На обед уместно сытное горячее"

    parts = [message]
    if harmony:
        parts.append(harmony)
    if schedule:
        parts.append(schedule)

    prefer = ctx.prefer_groups[0] if ctx.prefer_groups else "Горячие блюда"
    balance = _BALANCE_HINTS.get(prefer, "")
    if missing:
        balance = f"Добавьте «радугу»: {', '.join(missing[:2])}. {balance}".strip()

    return {
        "message": " · ".join(parts[:3]),
        "balance_hint": balance,
        "suggestion": prefer,
        "personalized": user.wellness_consent,
        "activity_level": user.activity_level or "moderate",
        "activity_label": _ACTIVITY_LABELS.get(user.activity_level or "moderate", "умеренная"),
        "calorie_target": daily_target,
        "calories_today": day.kcal_total,
        "calories_left": kcal_left,
        "meal_budget": meal_budget,
        "meal_calories_left": meal_left,
        "protein_g": day.protein_g,
        "carbs_g": day.carbs_g,
        "fat_g": day.fat_g,
        "water_glasses": day.water_glasses,
        "water_target": 8,
        "water_reminder": water or "",
        "meal_schedule": schedule or "",
        "harmony_hint": harmony,
        "rainbow_progress": rainbow_progress(day),
        "rainbow_missing": missing,
        "rainbow": {c: day.rainbow.get(c, 0) for c in RAINBOW_ORDER},
        "meal_bucket": ctx.bucket,
    }


async def wellness_tip(session: AsyncSession, user: User) -> dict:
    snap = await build_wellness_snapshot(session, user)
    if user.diet_preference:
        snap["message"] = f"{snap['message']} ({user.diet_preference})".strip()
    return snap


def wellness_score_for_food(
    food,
    *,
    user: User,
    day,
    meal_ctx,
) -> int:
    if not user.wellness_consent:
        return 0
    nut = estimate_food_nutrients(
        food.name,
        food.category,
        food.ingredients or "",
        food.portions or 1,
    )
    prefer = meal_ctx.prefer_groups[0] if meal_ctx.prefer_groups else None
    return score_food_for_wellness(
        nut,
        day=day,
        bucket=meal_ctx.bucket,
        activity=user.activity_level,
        prefer_group=prefer,
    )


def balance_hint_for_intent(cat_hint: dict) -> str:
    if cat_hint.get("score", 0) < 1 or cat_hint.get("group") == "Разное":
        return ""
    group = cat_hint["group"]
    return _BALANCE_HINTS.get(group, "")


async def harmonious_recommendations(
    session: AsyncSession,
    user: User,
    *,
    limit: int = 12,
    prefer_groups: list[str] | None = None,
) -> list[tuple]:
    from backend.services.memory_service import preferred_groups

    memory = await preferred_groups(session, user.id)
    ctx = build_meal_context(memory_groups=memory, user=user)
    prefer_group = (prefer_groups or list(ctx.prefer_groups) or [None])[0] or ctx.prefer_groups[0]

    all_recs = await ai_analyst_service.get_recommendations(session, user, limit=limit * 4)
    _, day = await get_day_nutrition(session, user)

    scored: list[tuple] = []
    for item in all_recs:
        food = item[0]
        if not food_matches_diet(food.name, food.category, user.diet_preference):
            continue
        group = food_group(food.category)
        base = 2 if group == prefer_group else 0
        if user.wellness_consent:
            base += wellness_score_for_food(food, user=user, day=day, meal_ctx=ctx)
        scored.append((base, item))

    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:limit]]


def wellness_response(user: User, snap: dict) -> dict:
    return {
        "wellness_consent": user.wellness_consent,
        "diet_preference": user.diet_preference,
        "activity_level": user.activity_level or "moderate",
        "message": snap.get("message", ""),
        "balance_hint": snap.get("balance_hint", ""),
        "suggestion": snap.get("suggestion", ""),
        "calorie_target": snap.get("calorie_target", 0),
        "calories_today": snap.get("calories_today", 0),
        "calories_left": snap.get("calories_left", 0),
        "meal_budget": snap.get("meal_budget", 0),
        "protein_g": snap.get("protein_g", 0),
        "carbs_g": snap.get("carbs_g", 0),
        "fat_g": snap.get("fat_g", 0),
        "water_glasses": snap.get("water_glasses", 0),
        "water_target": snap.get("water_target", 8),
        "water_reminder": snap.get("water_reminder", ""),
        "meal_schedule": snap.get("meal_schedule", ""),
        "harmony_hint": snap.get("harmony_hint", ""),
        "rainbow_progress": snap.get("rainbow_progress", 0),
        "rainbow_missing": snap.get("rainbow_missing", []),
        "rainbow": snap.get("rainbow", {}),
    }


async def recipe_hints_for_cook(
    session: AsyncSession,
    cook: User,
    *,
    context: str = "",
) -> list[str]:
    foods = await food_service.get_cook_foods(session, cook.id, include_inactive=True)
    existing_cats = {normalize_category(f.category) for f in foods}

    cat = categorize_text(query=context) if context.strip() else None
    hints: list[str] = []

    if cat and cat.get("score", 0) >= 1:
        key = cat["category"]
        for idea in _RECIPE_IDEAS.get(key, []):
            hints.append(idea)
        if not hints and cat["group"] != "Разное":
            hints.append(f"Спрос есть на «{cat['label']}» — добавьте блюдо в эту тему.")

    if not hints:
        for cat_name, ideas in _RECIPE_IDEAS.items():
            sample_path = f"Горячие блюда{SEP}{cat_name}" if cat_name in ("Супы", "Основные") else cat_name
            if not any(sample_path in p or cat_name in p for p in existing_cats):
                hints.append(ideas[0])
            if len(hints) >= 3:
                break

    if not hints:
        hints = [
            "Сезонный суп из свежих овощей",
            "Салат с местными продуктами",
            "Домашняя выпечка без лишнего сахара",
        ]

    return hints[:4]


async def feed_wellness_context(session: AsyncSession, user: User) -> dict | None:
    if not user.wellness_consent:
        return None
    snap = await build_wellness_snapshot(session, user)
    return {
        "calorie_summary": f"{snap['calories_today']} / {snap['calorie_target']} ккал",
        "meal_budget_label": f"~{snap['meal_budget']} ккал на {snap['meal_bucket']}",
        "water_reminder": snap.get("water_reminder") or "",
        "harmony_hint": snap.get("harmony_hint") or "",
        "rainbow_progress": snap["rainbow_progress"],
    }
