"""Оценка калорий, макросов, «радуги» и гармонии приёмов пищи — без внешних API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from backend.utils.categories import SEP, food_group, normalize_category

ActivityLevel = Literal["sedentary", "light", "moderate", "active", "intense"]

RAINBOW_ORDER = ("red", "orange", "yellow", "green", "purple", "white")

_ACTIVITY_KCAL: dict[str, int] = {
    "sedentary": 1900,
    "light": 2100,
    "moderate": 2300,
    "active": 2600,
    "intense": 2900,
}

_MEAL_SHARE: dict[str, float] = {
    "morning": 0.25,
    "lunch": 0.35,
    "afternoon": 0.12,
    "evening": 0.23,
    "night": 0.05,
}

_COLOR_MARKERS: dict[str, tuple[str, ...]] = {
    "red": (
        "томат", "помидор", "свёкл", "свекл", "клубник", "вишн", "ягод", "мяс", "говядин",
        "баран", "свинин", "перец красн", "red", "beet", "berry", "meat",
    ),
    "orange": (
        "морков", "тыкв", "апельсин", "мандарин", "хурм", "абрик", "orange", "carrot", "pumpkin",
    ),
    "yellow": (
        "кукуруз", "банан", "лимон", "сыр", "яйц", "масло", "куриц", "кукуруз", "corn", "egg", "cheese",
    ),
    "green": (
        "салат", "огурец", "брокколи", "шпинат", "зелень", "укроп", "петрушк", "капуст", "авокадо",
        "green", "herb", "spinach", "broccoli",
    ),
    "purple": (
        "баклажан", "черн", "слив", "виноград", "капуста красн", "eggplant", "plum", "grape", "purple",
    ),
    "white": (
        "рис", "картоф", "молок", "творог", "сметан", "лук", "чеснок", "тофу", "кускус", "rice", "potato",
        "milk", "tofu",
    ),
}

_GROUP_KCAL: dict[str, int] = {
    "Горячие блюда": 520,
    "Закуски и салаты": 240,
    "Выпечка и сладкое": 380,
    "На каждый день": 320,
}

_SUB_KCAL: dict[str, int] = {
    "Супы": 300,
    "Салаты": 200,
    "Основные": 560,
    "Десерт": 420,
    "Выпечка": 340,
    "Завтраки": 380,
}


@dataclass(frozen=True)
class FoodNutrients:
    kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    colors: tuple[str, ...]
    group: str
    is_heavy: bool
    is_light: bool


@dataclass
class DayNutrition:
    date_key: str
    kcal_total: int = 0
    protein_g: int = 0
    carbs_g: int = 0
    fat_g: int = 0
    rainbow: dict[str, int] = field(default_factory=lambda: {c: 0 for c in RAINBOW_ORDER})
    meals: list[dict] = field(default_factory=list)
    water_glasses: int = 0
    last_water_at: str | None = None
    last_meal_group: str | None = None
    last_meal_bucket: str | None = None


def daily_calorie_target(activity: str | None) -> int:
    key = (activity or "moderate").lower()
    if key not in _ACTIVITY_KCAL:
        key = "moderate"
    return _ACTIVITY_KCAL[key]


def meal_calorie_budget(bucket: str, activity: str | None) -> int:
    daily = daily_calorie_target(activity)
    share = _MEAL_SHARE.get(bucket, 0.25)
    return max(120, int(daily * share))


def detect_colors(blob: str) -> tuple[str, ...]:
    low = blob.lower()
    found: list[str] = []
    for color, markers in _COLOR_MARKERS.items():
        if any(m in low for m in markers):
            found.append(color)
    if not found:
        grp = food_group(blob) if SEP in blob or blob in _GROUP_KCAL else ""
        if grp == "Закуски и салаты":
            found.append("green")
        elif grp == "Горячие блюда":
            found.extend(["yellow", "white"])
        elif grp == "Выпечка и сладкое":
            found.append("yellow")
    return tuple(dict.fromkeys(found))


def estimate_food_nutrients(name: str, category: str, ingredients: str = "", portions: int = 1) -> FoodNutrients:
    path = normalize_category(category)
    grp = food_group(path)
    sub = path.split(SEP)[-1] if SEP in path else path
    base = _SUB_KCAL.get(sub) or _GROUP_KCAL.get(grp, 400)

    blob = f"{name} {ingredients} {category}"
    low = blob.lower()

    if any(w in low for w in ("жарен", "фри", "паниров", "deep")):
        base += 90
    if any(w in low for w in ("сливоч", "сметан", "майонез", "cream")):
        base += 70
    if any(w in low for w in ("запечён", "запечен", "паров", "на пару", "гриль")):
        base -= 40
    if any(w in low for w in ("лёгк", "легк", "диет", "овощ")):
        base -= 50
    if "десерт" in low or "торт" in low:
        base += 60

    kcal = max(80, int(base * max(1, min(portions, 3)) ** 0.5))
    colors = detect_colors(blob)
    heavy = grp in {"Горячие блюда", "Выпечка и сладкое"} and kcal >= 400
    light = grp in {"Закуски и салаты"} or kcal <= 280 or "Суп" in path

    protein = max(5, int(kcal * (0.22 if heavy else 0.15)))
    fat = max(3, int(kcal * (0.32 if "десерт" in low or grp == "Выпечка и сладкое" else 0.24)))
    carbs = max(8, int((kcal - protein * 4 - fat * 9) / 4))

    return FoodNutrients(
        kcal=kcal,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        colors=colors,
        group=grp,
        is_heavy=heavy,
        is_light=light,
    )


def missing_rainbow_colors(day: DayNutrition) -> list[str]:
    return [c for c in RAINBOW_ORDER if day.rainbow.get(c, 0) < 1]


def rainbow_progress(day: DayNutrition) -> int:
    hit = sum(1 for c in RAINBOW_ORDER if day.rainbow.get(c, 0) > 0)
    return int(round(100 * hit / len(RAINBOW_ORDER)))


def harmony_hint(day: DayNutrition, bucket: str, prefer_group: str | None) -> str:
    missing = missing_rainbow_colors(day)
    parts: list[str] = []

    if day.last_meal_group in {"Горячие блюда", "Выпечка и сладкое"} and bucket in ("afternoon", "evening", "night"):
        parts.append("После сытного — добавьте салат или суп")
    elif day.last_meal_group in {"Закуски и салаты"} and bucket == "lunch":
        parts.append("К лёгкому приёму на обед уместно горячее")
    elif not day.meals and bucket == "lunch":
        parts.append("Первый приём дня — сбалансируйте белок и овощи")

    if missing:
        color_ru = {
            "red": "красные",
            "orange": "оранжевые",
            "yellow": "жёлтые",
            "green": "зелёные",
            "purple": "фиолетовые",
            "white": "белые",
        }
        parts.append(f"В рационе не хватает {color_ru.get(missing[0], missing[0])} продуктов")

    if prefer_group and prefer_group != day.last_meal_group:
        parts.append(f"Сейчас логично: {prefer_group.lower()}")

    return " · ".join(parts[:2])


def water_reminder_text(hour: int, glasses: int, last_water_hour: int | None) -> str | None:
    if hour < 8 or hour > 22:
        return None
    target = 8
    if glasses >= target:
        return None
    if last_water_hour is not None and hour - last_water_hour < 2 and glasses > 0:
        return None
    left = target - glasses
    if hour >= 12 and glasses < 3:
        return f"Выпейте воды — сегодня {glasses} из {target} стаканов"
    if left <= 2:
        return f"До нормы воды осталось {left} стак."
    return f"Стакан воды — {glasses}/{target} за день"


def meal_schedule_hint(bucket: str, hour: int) -> str | None:
    if bucket == "morning" and hour > 10:
        return "Завтрак лучше до 10:00 — метаболизм активнее утром"
    if bucket == "lunch" and hour > 15:
        return "Обед после 15:00 — выбирайте лёгкие блюда"
    if bucket == "evening" and hour >= 21:
        return "Поздний ужин — суп или салат, без тяжёлого"
    if bucket == "night":
        return "Ночной перекус — только лёгкое, за 2 ч до сна"
    if bucket == "lunch" and 12 <= hour <= 14:
        return "Окно обеда — основная энергия дня"
    return None


def score_food_for_wellness(
    nut: FoodNutrients,
    *,
    day: DayNutrition,
    bucket: str,
    activity: str | None,
    prefer_group: str | None,
) -> int:
    score = 0
    budget = meal_calorie_budget(bucket, activity)

    for c in nut.colors:
        if day.rainbow.get(c, 0) < 1:
            score += 9

    if prefer_group and nut.group == prefer_group:
        score += 6

    if day.last_meal_group in {"Горячие блюда", "Выпечка и сладкое"} and nut.is_light:
        score += 12
    if day.last_meal_group in {"Закуски и салаты"} and bucket == "lunch" and nut.group == "Горячие блюда":
        score += 10

    if nut.kcal <= budget:
        score += 5
    elif nut.kcal > int(budget * 1.35):
        score -= 10

    if bucket in ("evening", "night") and nut.is_heavy:
        score -= 8
    if bucket == "morning" and nut.group == "Выпечка и сладкое" and "Десерт" not in nut.group:
        score += 4

    day_kcal = day.kcal_total
    daily = daily_calorie_target(activity)
    if day_kcal > daily * 0.92 and nut.kcal > 350:
        score -= 6
    if day_kcal < daily * 0.35 and bucket in ("lunch", "evening") and nut.kcal >= 300:
        score += 4

    return score


def apply_meal_to_day(day: DayNutrition, nut: FoodNutrients, *, bucket: str) -> None:
    day.kcal_total += nut.kcal
    day.protein_g += nut.protein_g
    day.carbs_g += nut.carbs_g
    day.fat_g += nut.fat_g
    for c in nut.colors:
        day.rainbow[c] = day.rainbow.get(c, 0) + 1
    day.last_meal_group = nut.group
    day.last_meal_bucket = bucket
    day.meals.append(
        {
            "bucket": bucket,
            "group": nut.group,
            "kcal": nut.kcal,
            "colors": list(nut.colors),
        }
    )
