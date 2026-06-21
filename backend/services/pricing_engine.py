"""Расчёт справедливой цены: регион + сезон + расходники."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.utils.ingredient_costs import (
    CATEGORY_BASE_COST,
    INGREDIENT_BASE_STARS,
    INGREDIENT_SEASON_GROUP,
    SEASON_CATEGORY_MULT,
    SEASON_INGREDIENT_MULT,
)

VERDICT_LABELS = {
    "underpriced": "Ниже рынка",
    "fair": "Справедливая цена",
    "premium": "Премиум",
    "overpriced": "Завышена",
    "below_cost": "Ниже себестоимости",
}


def month_to_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Зима"
    if month in (3, 4, 5):
        return "Весна"
    if month in (6, 7, 8):
        return "Лето"
    return "Осень"


def category_season_factor(category: str, month: int) -> float:
    season = month_to_season(month)
    return SEASON_CATEGORY_MULT.get(season, {}).get(category, 1.0)


def _ingredient_season_mult(ingredient_key: str, season: str) -> float:
    group = INGREDIENT_SEASON_GROUP.get(ingredient_key, "default")
    return SEASON_INGREDIENT_MULT.get(season, {}).get(group, SEASON_INGREDIENT_MULT[season]["default"])


def parse_ingredient_tokens(text: str) -> list[str]:
    if not text.strip():
        return []
    raw = text.replace(";", ",").replace("\n", ",")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def match_ingredient(token: str) -> str | None:
    if token in INGREDIENT_BASE_STARS:
        return token
    for key in INGREDIENT_BASE_STARS:
        if key in token or token in key:
            return key
    return None


@dataclass
class IngredientEstimate:
    total_cost: float
    items: list[str] = field(default_factory=list)
    used_fallback: bool = False


def estimate_ingredient_cost(
    ingredients_text: str,
    category: str,
    portions: int,
    month: int,
) -> IngredientEstimate:
    season = month_to_season(month)
    tokens = parse_ingredient_tokens(ingredients_text)
    matched: list[tuple[str, float]] = []

    for token in tokens:
        key = match_ingredient(token)
        if key is None:
            continue
        base = INGREDIENT_BASE_STARS[key]
        mult = _ingredient_season_mult(key, season)
        matched.append((key, base * mult))

    if not matched:
        base = CATEGORY_BASE_COST.get(category, 50)
        season_mult = category_season_factor(category, month)
        per_portion = base * season_mult
        total = round(per_portion * max(portions, 1), 2)
        return IngredientEstimate(
            total_cost=total,
            items=[f"базовая оценка категории «{category}» ({season.lower()})"],
            used_fallback=True,
        )

    per_portion = sum(cost for _, cost in matched)
    total = round(per_portion * max(portions, 1), 2)
    items = [f"{name} ~{int(cost)} ⭐" for name, cost in matched]
    return IngredientEstimate(total_cost=total, items=items, used_fallback=False)


def labor_cost_stars(cooking_time_minutes: int) -> float:
    """Труд и электричество/газ за приготовление."""
    return round(max(8.0, cooking_time_minutes * 0.45), 2)


@dataclass
class PriceRecommendation:
    regional_avg_price: float
    seasonal_market_price: float
    season_name: str
    season_factor: float
    ingredient_cost: float
    labor_cost: float
    cook_minimum: float
    fair_price: float
    suggested_price_min: float
    suggested_price_max: float
    verdict: str
    price_score: int
    summary: str
    ingredient_items: list[str]
    region_label: str
    cook_margin_percent: float
    buyer_savings_hint: str


def _price_verdict(price: float, fair: float, cook_min: float) -> tuple[str, int]:
    if price < cook_min * 0.95:
        return "below_cost", max(5, int(40 - (cook_min - price) / cook_min * 50))
    if fair <= 0:
        return "fair", 75
    ratio = price / fair
    if ratio < 0.82:
        return "underpriced", min(100, int(90 + (0.82 - ratio) * 30))
    if ratio <= 1.08:
        return "fair", int(100 - abs(ratio - 1.0) * 100)
    if ratio <= 1.25:
        return "premium", int(max(40, 78 - (ratio - 1.08) * 80))
    return "overpriced", int(max(8, 42 - (ratio - 1.25) * 60))


def compute_fair_price(
    regional_avg: float,
    category: str,
    *,
    ingredients: str = "",
    portions: int = 1,
    cooking_time_minutes: int = 30,
    current_price: float | None = None,
    month: int | None = None,
    region_label: str = "ваш регион",
    dish_name: str = "",
) -> PriceRecommendation:
    month = month or datetime.now(timezone.utc).month
    season = month_to_season(month)
    season_factor = category_season_factor(category, month)

    # Реальная средняя по региону; если мало данных — используем категорийный ориентир.
    if regional_avg <= 0:
        regional_avg = CATEGORY_BASE_COST.get(category, 50) * 1.35

    seasonal_market = round(regional_avg * season_factor, 2)

    # Себестоимость: расходники + сезон + труд.
    ing = estimate_ingredient_cost(
        ingredients or dish_name,
        category,
        portions,
        month,
    )
    labor = labor_cost_stars(cooking_time_minutes)
    cook_minimum = round(ing.total_cost + labor * 1.1, 2)  # +10% на упаковку/газ

    # Справедливая цена: повар не в убытке, покупатель не переплачивает рынок.
    market_cap = round(seasonal_market * 1.10, 2)
    if cook_minimum > seasonal_market * 1.15:
        # Дорогие продукты вне сезона — честная цена выше рынка.
        fair = round(max(cook_minimum * 1.08, seasonal_market), 2)
        buyer_hint = "Сезон повышает стоимость продуктов — цена повара оправдана."
    elif cook_minimum < seasonal_market * 0.65:
        fair = round(seasonal_market * 0.94, 2)
        buyer_hint = "Хорошая маржа для повара и выгодная цена для покупателя."
    else:
        fair = round((cook_minimum * 1.06 + seasonal_market) / 2, 2)
        buyer_hint = "Баланс: повар покрывает расходы, покупатель платит около рынка."

    fair = min(fair, market_cap)
    fair = max(fair, cook_minimum)

    suggested_min = max(1, round(max(cook_minimum, fair * 0.96)))
    suggested_max = max(suggested_min + 1, round(min(fair * 1.05, market_cap)))

    verdict, score = "fair", 80
    if current_price is not None and current_price > 0:
        verdict, score = _price_verdict(current_price, fair, cook_minimum)

    margin = round((fair - ing.total_cost - labor) / fair * 100, 1) if fair > 0 else 0.0

    ing_note = ", ".join(ing.items[:5])
    if len(ing.items) > 5:
        ing_note += "…"

    summary_parts = [
        f"Регион ({region_label}): средняя {int(regional_avg)} ⭐.",
        f"{season}: рынок ×{season_factor:.2f} → ~{int(seasonal_market)} ⭐.",
        f"Расходники ~{int(ing.total_cost)} ⭐ + работа ~{int(labor)} ⭐.",
        f"Минимум для повара {int(cook_minimum)} ⭐, справедливо {int(fair)} ⭐ ({suggested_min}–{suggested_max}).",
    ]
    if ing.items and not ing.used_fallback:
        summary_parts.insert(3, f"Состав: {ing_note}.")

    return PriceRecommendation(
        regional_avg_price=round(regional_avg, 2),
        seasonal_market_price=seasonal_market,
        season_name=season,
        season_factor=round(season_factor, 3),
        ingredient_cost=ing.total_cost,
        labor_cost=labor,
        cook_minimum=cook_minimum,
        fair_price=fair,
        suggested_price_min=float(suggested_min),
        suggested_price_max=float(suggested_max),
        verdict=verdict,
        price_score=score,
        summary=" ".join(summary_parts),
        ingredient_items=ing.items,
        region_label=region_label,
        cook_margin_percent=margin,
        buyer_savings_hint=buyer_hint,
    )
