"""Гармоничные рекомендации и подсказки по питанию — только с согласия пользователя."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Food, User
from backend.services import ai_analyst_service, food_service
from backend.utils.categories import SEP, categorize_text, food_group, normalize_category

# Натуральные сочетания: группа → что дополняет рацион
_BALANCE_HINTS: dict[str, str] = {
    "Горячие блюда": "Добавьте салат или лёгкий напиток — баланс тепла и свежести.",
    "Выпечка и сладкое": "После сладкого хорошо сочетается тёплый чай или лёгкий суп.",
    "Закуски и салаты": "К салату гармонично подойдёт сытное горячее или цельный хлеб.",
    "На каждый день": "Чередуйте лёгкие завтраки с полноценными обедами — так проще держать ритм.",
}

_LIGHT_GROUPS = {"Закуски и салаты", "На каждый день"}
_HEAVY_GROUPS = {"Горячие блюда", "Выпечка и сладкое"}

_RECIPE_IDEAS: dict[str, list[str]] = {
    "Супы": [
        "Домашний борщ на говядине с запечёнными овощами",
        "Крем-суп из тыквы с имбирём — без сливок, на овощном бульоне",
        "Лёгкий куриный бульон с зеленью и домашней лапшой",
    ],
    "Салаты": [
        "Салат из сезонных овощей с оливковым маслом и зеленью",
        "Винегрет с ферментированной капустой — просто и полезно",
    ],
    "Основные": [
        "Запечённая рыба с лимоном и травами",
        "Тушёные овощи с крупой — сытно и натурально",
    ],
    "Выпечка": [
        "Цельнозерновой хлеб на закваске",
        "Овсяные оладьи без сахара — с ягодами",
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


async def wellness_tip(session: AsyncSession, user: User) -> dict:
    if not user.wellness_consent:
        return {
            "consented": False,
            "message": "",
            "suggestion": None,
        }

    bucket = _hour_bucket()
    recent = await _recent_search_groups(session, user.id)

    if bucket == "morning":
        msg = "Утро — время лёгкого и тёплого: каша, омлет или свежий чай."
        prefer = "На каждый день"
    elif bucket == "lunch":
        msg = "Обед — сытное горячее и салат дают энергию без тяжести."
        prefer = "Горячие блюда"
    elif bucket == "evening":
        msg = "Вечер — умеренная порция и тёплое блюдо помогают спокойно завершить день."
        prefer = "Горячие блюда"
    else:
        msg = "Поздний перекус — лучше лёгкое: чай, салат или суп."
        prefer = "Закуски и салаты"

    if recent:
        last = recent[0]
        if last in _HEAVY_GROUPS and bucket in ("evening", "night"):
            msg = "Вчера было сытно — сегодня можно выбрать что-то полегче: суп или салат."
            prefer = "Закуски и салаты"
        elif last in _LIGHT_GROUPS and bucket == "lunch":
            msg = "После лёгких блюд на обед хорошо подойдёт сытное горячее."
            prefer = "Горячие блюда"

    if user.diet_preference:
        msg = f"{msg} Учитываю ваши предпочтения: {user.diet_preference}."

    return {
        "consented": True,
        "message": msg,
        "suggestion": prefer,
        "balance_hint": _BALANCE_HINTS.get(prefer, ""),
    }


async def harmonious_recommendations(
    session: AsyncSession,
    user: User,
    *,
    limit: int = 12,
) -> list[tuple]:
    """Рекомендации с учётом времени суток и согласия на wellness."""
    if not user.wellness_consent:
        return []

    tip = await wellness_tip(session, user)
    prefer_group = tip.get("suggestion") or "Горячие блюда"

    all_recs = await ai_analyst_service.get_recommendations(session, user, limit=limit * 2)
    matched: list[tuple] = []
    rest: list[tuple] = []
    for item in all_recs:
        food = item[0]
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
    """Контекстные идеи блюд для повара — по теме, без лишнего."""
    foods = await food_service.get_cook_foods(session, cook.id, include_inactive=True)
    existing_cats = {normalize_category(f.category) for f in foods}

    cat = categorize_text(query=context) if context.strip() else None
    hints: list[str] = []

    if cat and cat.get("score", 0) >= 1:
        key = cat["category"]
        for idea in _RECIPE_IDEAS.get(key, []):
            hints.append(idea)
        if not hints and cat["group"] != "Разное":
            hints.append(
                f"Добавьте блюдо в категории «{cat['label']}» — сейчас на это есть спрос."
            )

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
