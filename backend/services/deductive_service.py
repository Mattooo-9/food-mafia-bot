"""Единая дедуктивная модель пользователя — все сигналы → один вывод."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from backend.i18n.messages import normalize_locale, t
from backend.models import User
from backend.services.meal_context import MealContext, local_now
from backend.services.memory_service import get_memory, _loads_queries
from backend.services.nutrient_engine import (
    daily_calorie_target,
    harmony_hint,
    meal_calorie_budget,
    missing_rainbow_colors,
    water_reminder_text,
)
from backend.services.wellness_tracker import get_day_nutrition

_DIET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"веган|vegan", re.I), "vegan"),
    (re.compile(r"без\s*мяс|постн|vegetarian", re.I), "no_meat"),
    (re.compile(r"без\s*слад|мало\s*сахар|no\s*sugar", re.I), "low_sugar"),
    (re.compile(r"без\s*лакт|лактоз|lactose", re.I), "no_lactose"),
    (re.compile(r"лёгк|легк|диет|light", re.I), "light"),
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


def _user_locale(user: User) -> str:
    return normalize_locale(user.language_code, user.locale)


async def sync_user_profile(session: AsyncSession, user: User) -> User:
    """Тихо выводит активность и рацион; wellness — после нескольких поисков."""
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
    if (mem.searches_count or 0) >= 2 and not user.wellness_consent:
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
    """Одна строка контекста — без повторов."""
    loc = _user_locale(user)

    if state == "no_geo":
        return t(loc, "companion.no_geo")

    if state == "search_empty" and query.strip():
        return t(loc, "companion.search_empty")

    if state == "no_supply":
        return t(loc, "companion.no_supply")

    if not user.wellness_consent or meal_ctx is None:
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
        meal = t(loc, f"meal.{meal_ctx.bucket}")
        parts.append(t(loc, "hint.kcal_left", meal=meal, kcal=str(max(0, min(budget, kcal_left)))))
    elif harmony:
        parts.append(harmony.split(" · ")[0])
    missing = missing_rainbow_colors(day)
    if missing and not parts:
        parts.append(t(loc, "hint.rainbow", color=missing[0]))
    if water and len(parts) < 2:
        parts.append(water)

    if not parts and state == "browse":
        return ""

    return " · ".join(parts[:2])[:140]
