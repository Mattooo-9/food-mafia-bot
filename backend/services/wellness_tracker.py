"""Дневной трекер питания и воды — в user_memory.wellness_state."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserMemory
from backend.services.meal_context import local_now
from backend.services.memory_service import get_memory
from backend.services.nutrient_engine import (
    RAINBOW_ORDER,
    DayNutrition,
    apply_meal_to_day,
    estimate_food_nutrients,
)


def _today_key(user: User) -> str:
    return local_now(user).strftime("%Y-%m-%d")


def _empty_day(date_key: str) -> DayNutrition:
    return DayNutrition(date_key=date_key)


def _parse_state(raw: str | None, date_key: str) -> DayNutrition:
    if not raw:
        return _empty_day(date_key)
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("date_key") != date_key:
            return _empty_day(date_key)
        rainbow = {c: int(data.get("rainbow", {}).get(c, 0)) for c in RAINBOW_ORDER}
        return DayNutrition(
            date_key=date_key,
            kcal_total=int(data.get("kcal_total", 0)),
            protein_g=int(data.get("protein_g", 0)),
            carbs_g=int(data.get("carbs_g", 0)),
            fat_g=int(data.get("fat_g", 0)),
            rainbow=rainbow,
            meals=list(data.get("meals", []))[:12],
            water_glasses=int(data.get("water_glasses", 0)),
            last_water_at=data.get("last_water_at"),
            last_meal_group=data.get("last_meal_group"),
            last_meal_bucket=data.get("last_meal_bucket"),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return _empty_day(date_key)


def _dump_state(day: DayNutrition) -> str:
    return json.dumps(
        {
            "date_key": day.date_key,
            "kcal_total": day.kcal_total,
            "protein_g": day.protein_g,
            "carbs_g": day.carbs_g,
            "fat_g": day.fat_g,
            "rainbow": day.rainbow,
            "meals": day.meals[-8:],
            "water_glasses": day.water_glasses,
            "last_water_at": day.last_water_at,
            "last_meal_group": day.last_meal_group,
            "last_meal_bucket": day.last_meal_bucket,
        },
        ensure_ascii=False,
    )


async def get_day_nutrition(session: AsyncSession, user: User) -> tuple[UserMemory, DayNutrition]:
    mem = await get_memory(session, user.id)
    key = _today_key(user)
    day = _parse_state(getattr(mem, "wellness_state", None), key)
    if day.date_key != key:
        day = _empty_day(key)
    return mem, day


async def persist_day(session: AsyncSession, mem: UserMemory, day: DayNutrition) -> None:
    mem.wellness_state = _dump_state(day)
    await session.flush()


async def log_food_meal(
    session: AsyncSession,
    user: User,
    *,
    name: str,
    category: str,
    ingredients: str = "",
    portions: int = 1,
    bucket: str | None = None,
) -> DayNutrition:
    from backend.services.meal_context import build_meal_context

    mem, day = await get_day_nutrition(session, user)
    ctx = build_meal_context(user=user)
    meal_bucket = bucket or ctx.bucket
    nut = estimate_food_nutrients(name, category, ingredients, portions)
    apply_meal_to_day(day, nut, bucket=meal_bucket)
    await persist_day(session, mem, day)
    return day


async def log_water(session: AsyncSession, user: User) -> DayNutrition:
    mem, day = await get_day_nutrition(session, user)
    day.water_glasses = min(12, day.water_glasses + 1)
    day.last_water_at = datetime.utcnow().isoformat()
    await persist_day(session, mem, day)
    return day
