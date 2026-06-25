"""Единая дедуктивная модель пользователя — все сигналы → один вывод."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.services.meal_context import MealContext, local_now
from backend.services.memory_service import get_memory, _loads_counts, _loads_queries
from backend.services.nutrient_engine import (
    daily_calorie_target,
    harmony_hint,
    meal_calorie_budget,
    missing_rainbow_colors,
    water_reminder_text,
)
from backend.services.wellness_tracker import get_day_nutrition

_DIET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"веган|vegan", re.I), "веган"),
    (re.compile(r"без\s*мяс|постн", re.I), "без мяса"),
    (re.compile(r"без\s*слад|мало\s*сахар", re.I), "без сладкого"),
    (re.compile(r"без\s*лакт|лактоз", re.I), "без лактозы"),
    (re.compile(r"лёгк|легк|диет", re.I), "лёгкое"),
)


def _infer_activity(mem) -> str:
    orders = mem.orders_delivered or 0
    searches = mem.searches_count or 0
    if orders >= 20 or (orders >= 8 and searches >= 40):
        return "active"
    if orders >= 10 or searches >= 25:
        return "moderate"
    if orders >= 3 or searches >= 10:
        return "light"
    return "sedentary"


def _infer_diet(mem, user: User) -> str | None:
    if user.diet_preference:
        return user.diet_preference
    blob = " ".join(_loads_queries(mem.recent_queries)).lower()
    for pattern, label in _DIET_PATTERNS:
        if pattern.search(blob):
            return label
    return None


def _estimate_water_glasses(hour: int, meals_count: int, kcal_today: int) -> int:
    base = max(0, min(8, (hour - 7) // 2))
    base += min(2, meals_count)
    if kcal_today > 1200:
        base += 1
    return min(8, base)


async def sync_user_profile(session: AsyncSession, user: User) -> User:
    """Тихо выводит активность, рацион и включает умный режим."""
    mem = await get_memory(session, user.id)
    activity = _infer_activity(mem)
    diet = _infer_diet(mem, user)
    changed = False
    if user.activity_level != activity:
        user.activity_level = activity
        changed = True
    if diet and user.diet_preference != diet:
        user.diet_preference = diet
        changed = True
    if not user.wellness_consent:
        user.wellness_consent = True
        changed = True
    if changed:
        await session.commit()
    return user


async def feed_companion(
    session: AsyncSession,
    user: User,
    *,
    state: str,
    meal_ctx: MealContext | None,
    has_location: bool,
    query: str,
) -> str:
    """Одна строка контекста — без повторов и банальностей."""
    if state == "no_geo":
        return "Включите «Гео» в шапке — покажем блюда рядом."

    if state == "search_empty" and query.strip():
        return "Такого нет в ленте — опишите запрос во вкладке «Заказы»."

    if state == "no_supply":
        return "Поваров рядом пока нет — загляните позже или оставьте запрос в «Заказах»."

    if meal_ctx is None:
        return ""

    now = local_now(user)
    _, day = await get_day_nutrition(session, user)
    est_water = _estimate_water_glasses(now.hour, len(day.meals), day.kcal_total)
    glasses = max(day.water_glasses, est_water)

    prefer = meal_ctx.prefer_groups[0] if meal_ctx.prefer_groups else None
    harmony = harmony_hint(day, meal_ctx.bucket, prefer)
    water = water_reminder_text(now.hour, glasses, None)

    daily = daily_calorie_target(user.activity_level)
    budget = meal_calorie_budget(meal_ctx.bucket, user.activity_level)
    kcal_left = daily - day.kcal_total

    parts: list[str] = []
    if kcal_left < budget and meal_ctx.bucket in ("lunch", "evening"):
        parts.append(f"На {meal_ctx.section_label.lower()} осталось ~{max(0, min(budget, kcal_left))} ккал")
    elif harmony:
        parts.append(harmony.split(" · ")[0])
    missing = missing_rainbow_colors(day)
    if missing and not parts:
        color_ru = {"red": "красные", "green": "зелёные", "orange": "оранжевые"}
        parts.append(f"Добавьте {color_ru.get(missing[0], missing[0])} овощи/фрукты")
    if water and len(parts) < 2:
        parts.append(water)

    if not parts and state == "browse":
        return ""

    return " · ".join(parts[:2])[:140]
