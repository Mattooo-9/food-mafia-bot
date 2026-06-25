"""Контекст приёма пищи: время, сезон, выходные — тихо управляет выдачей."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.utils.categories import categorize_text, excluded_groups_for

# Основная аудитория — РФ; zoneinfo есть в Python 3.9+
LOCAL_TZ = ZoneInfo("Europe/Moscow")

_LIGHT = "Закуски и салаты"
_HOT = "Горячие блюда"
_BAKERY = "Выпечка и сладкое"
_DAILY = "На каждый день"


@dataclass(frozen=True)
class MealContext:
    bucket: str
    hour: int
    is_weekend: bool
    season: str
    section_label: str
    search_placeholder: str
    prefer_groups: tuple[str, ...]
    suggest_chips: tuple[str, ...]
    max_distance_m: float | None
    prefer_fast: bool
    boost_online_cooks: bool


def local_now(user=None) -> datetime:
    if user is not None:
        from backend.utils.locale_tz import zone_for_user

        return datetime.now(zone_for_user(user))
    return datetime.now(LOCAL_TZ)


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def _hour_bucket(hour: int) -> str:
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 14:
        return "lunch"
    if 14 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def build_meal_context(
    *,
    memory_groups: list[str] | None = None,
    last_group: str | None = None,
    user=None,
) -> MealContext:
    now = local_now(user)
    hour = now.hour
    bucket = _hour_bucket(hour)
    weekend = now.weekday() >= 5
    season = _season(now.month)

    if bucket == "morning":
        label, placeholder = "Завтрак", "Завтрак, выпечка…"
        groups = (_DAILY, _BAKERY, _LIGHT)
        chips = ("Завтрак", "Выпечка", "Омлет") if not weekend else ("Бранч", "Выпечка", "Завтрак")
        dist, fast, online = 3500.0, True, True
    elif bucket == "lunch":
        label, placeholder = "Обед", "Суп, горячее…"
        groups = (_HOT, _LIGHT, _DAILY)
        chips = ("Обед", "Суп", "Салат")
        dist, fast, online = 2500.0, True, True
    elif bucket == "afternoon":
        label, placeholder = "Перекус", "Салат, выпечка…"
        groups = (_LIGHT, _BAKERY, _DAILY)
        chips = ("Салат", "Выпечка", "Перекус")
        dist, fast, online = 3000.0, True, False
    elif bucket == "evening":
        label, placeholder = "Ужин", "Ужин, суп…"
        groups = (_HOT, _LIGHT, _BAKERY)
        chips = ("Ужин", "Суп", "Салат")
        dist, fast, online = 5000.0, False, True
    else:
        label, placeholder = "Поздно", "Суп, лёгкое…"
        groups = (_LIGHT, _HOT, _DAILY)
        chips = ("Суп", "Салат")
        dist, fast, online = 2000.0, True, False

    if season == "winter" and _HOT not in groups:
        groups = (_HOT, *groups)
    if season == "summer" and _LIGHT not in groups[:2]:
        groups = (_LIGHT, *tuple(g for g in groups if g != _LIGHT))

    if last_group in (_HEAVY := {_HOT, _BAKERY}) and bucket in ("evening", "night"):
        groups = (_LIGHT, _HOT, _DAILY)
        chips = ("Суп", "Салат", *tuple(c for c in chips if c not in ("Ужин", "Обед")))

    merged_groups = list(groups)
    for g in memory_groups or []:
        if g not in merged_groups and g != "Разное":
            merged_groups.append(g)

    chip_list = list(chips)
    for g in (memory_groups or [])[:1]:
        chip = _group_chip(g)
        if chip.lower() not in {c.lower() for c in chip_list}:
            chip_list.insert(0, chip)

    return MealContext(
        bucket=bucket,
        hour=hour,
        is_weekend=weekend,
        season=season,
        section_label=label,
        search_placeholder=placeholder,
        prefer_groups=tuple(merged_groups[:4]),
        suggest_chips=tuple(chip_list[:4]),
        max_distance_m=dist,
        prefer_fast=fast,
        boost_online_cooks=online,
    )


def _group_chip(group: str) -> str:
    return {
        _HOT: "Суп",
        _LIGHT: "Салат",
        _BAKERY: "Выпечка",
        _DAILY: "Завтрак",
    }.get(group, group.split()[-1] if group else "Обед")


def meal_category_for_chip(chip: str) -> dict | None:
    cat = categorize_text(query=chip.lower())
    if cat.get("score", 0) >= 1 and cat.get("group") != "Разное":
        return cat
    return None


def apply_meal_to_intent(intent: dict, ctx: MealContext, *, has_query: bool) -> dict:
    """Подмешивает контекст в intent без лишнего текста для пользователя."""
    intent["meal_bucket"] = ctx.bucket
    intent["meal_season"] = ctx.season

    if has_query:
        return intent

    merged: list[str] = list(intent.get("prefer_groups_memory") or [])
    for g in ctx.prefer_groups:
        if g not in merged:
            merged.append(g)
    if merged:
        intent["prefer_groups_memory"] = merged[:4]

    if intent.get("max_distance_m") is None:
        intent["max_distance_m"] = ctx.max_distance_m
    elif ctx.max_distance_m and intent["max_distance_m"] > ctx.max_distance_m:
        intent["max_distance_m"] = ctx.max_distance_m

    if intent.get("vague") or not intent.get("query"):
        chip = ctx.suggest_chips[0] if ctx.suggest_chips else "Обед"
        meal_cat = meal_category_for_chip(chip)
        if meal_cat and not merged:
            intent["category_hint"] = meal_cat
            intent["category"] = meal_cat["path"]
            intent["exclude_groups"] = excluded_groups_for(meal_cat)
            intent["strict_category"] = False
            intent["vague"] = True

    if ctx.prefer_fast and intent.get("feed") == "nearby":
        labels = intent.setdefault("sort_labels", [])
        if not any("быстр" in lb for lb in labels):
            labels.append("быстрее готовят")

    return intent


def score_adjustments(
    *,
    ctx: MealContext,
    food_group_name: str,
    food_category: str,
    cooking_minutes: int,
    cook_online: bool,
) -> int:
    delta = 0
    if food_group_name in ctx.prefer_groups:
        delta += 12 - ctx.prefer_groups.index(food_group_name) * 3

    if ctx.prefer_fast:
        if cooking_minutes <= 25:
            delta += 10
        elif cooking_minutes <= 40:
            delta += 4
        elif cooking_minutes > 75:
            delta -= 6

    if ctx.bucket in ("evening", "night"):
        if food_group_name == _BAKERY and "Десерт" in food_category:
            delta -= 8
        if "Суп" in food_category or food_group_name == _LIGHT:
            delta += 6

    if ctx.bucket == "morning" and food_group_name == _BAKERY:
        delta += 8

    if ctx.season == "winter" and ("Суп" in food_category or "Борщ" in food_category):
        delta += 7
    if ctx.season == "summer" and food_group_name == _LIGHT:
        delta += 6

    if ctx.boost_online_cooks and cook_online:
        delta += 5

    if ctx.bucket == "lunch" and cooking_minutes > 60:
        delta -= 5

    return delta


def context_payload(ctx: MealContext) -> dict:
    return {
        "meal": ctx.bucket,
        "section_label": ctx.section_label,
        "search_placeholder": ctx.search_placeholder,
        "season": ctx.season,
        "is_weekend": ctx.is_weekend,
    }

# Re-export for nutrition_service compatibility
def hour_bucket() -> str:
    return _hour_bucket(local_now().hour)
