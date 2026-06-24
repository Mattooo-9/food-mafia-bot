"""Гармоничные рекомендации — работают всегда; история учитывается только с согласия."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services import ai_analyst_service, food_service
from backend.utils.categories import SEP, categorize_text, food_group, normalize_category

_BALANCE_HINTS: dict[str, str] = {
    "Горячие блюда": "К горячему хорошо добавить салат или тёплый напиток.",
    "Выпечка и сладкое": "Сладкое лучше в умеренной порции — дополните чаем или супом.",
    "Закуски и салаты": "Салату к месту сытное горячее или цельный хлеб.",
    "На каждый день": "Чередуйте лёгкие и сытные приёмы пищи — так проще держать баланс.",
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


def _hour_bucket() -> str:
    h = datetime.now(timezone.utc).hour
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 16:
        return "lunch"
    if 16 <= h < 21:
        return "evening"
    return "night"


def _base_tip_for_hour() -> tuple[str, str]:
    bucket = _hour_bucket()
    if bucket == "morning":
        return "Утро — лёгкий завтрак рядом.", "На каждый день"
    if bucket == "lunch":
        return "Обед — сытное горячее рядом.", "Горячие блюда"
    if bucket == "evening":
        return "Вечер — тёплое, без тяжести.", "Горячие блюда"
    return "Поздно — суп или салат.", "Закуски и салаты"


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


async def wellness_tip(session: AsyncSession, user: User) -> dict:
    msg, prefer = _base_tip_for_hour()
    personalized = False

    if user.wellness_consent:
        personalized = True
        recent = await _recent_search_groups(session, user.id)
        bucket = _hour_bucket()
        if recent:
            last = recent[0]
            if last in _HEAVY_GROUPS and bucket in ("evening", "night"):
                msg = "Недавно было сытно — сейчас уместнее суп или салат."
                prefer = "Закуски и салаты"
            elif last in _LIGHT_GROUPS and bucket == "lunch":
                msg = "После лёгкого — на обед логично сытное горячее."
                prefer = "Горячие блюда"

    if user.diet_preference:
        msg = f"{msg} ({user.diet_preference})."

    return {
        "personalized": personalized,
        "message": msg,
        "suggestion": prefer,
        "balance_hint": _BALANCE_HINTS.get(prefer, ""),
    }


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
    tip = await wellness_tip(session, user)
    prefer_group = (prefer_groups or [None])[0] or tip.get("suggestion") or "Горячие блюда"

    all_recs = await ai_analyst_service.get_recommendations(session, user, limit=limit * 3)
    matched: list[tuple] = []
    rest: list[tuple] = []
    for item in all_recs:
        food = item[0]
        if not food_matches_diet(food.name, food.category, user.diet_preference):
            continue
        group = food_group(food.category)
        if group == prefer_group:
            matched.append(item)
        else:
            rest.append(item)

    out = matched[:limit]
    if len(out) < limit:
        out.extend(rest[: limit - len(out)])
    return out


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
