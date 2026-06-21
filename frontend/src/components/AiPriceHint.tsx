import { useEffect, useState } from "react";
import { api, formatStars } from "../api";
import type { PriceSuggestion } from "../types";

interface Props {
  category: string;
  price: string;
  ingredients: string;
  portions: string;
  cookingTime: string;
  name: string;
}

export default function AiPriceHint({
  category,
  price,
  ingredients,
  portions,
  cookingTime,
  name,
}: Props) {
  const [hint, setHint] = useState<PriceSuggestion | null>(null);

  useEffect(() => {
    if (!category) return;
    const priceNum = Number(price);
    const timer = setTimeout(() => {
      void api
        .getPriceSuggestion(category, {
          price: priceNum > 0 ? priceNum : undefined,
          ingredients,
          portions: Math.max(1, Number(portions) || 1),
          cooking_time_minutes: Math.max(1, Number(cookingTime) || 30),
          name,
        })
        .then(setHint)
        .catch(() => setHint(null));
    }, 450);
    return () => clearTimeout(timer);
  }, [category, price, ingredients, portions, cookingTime, name]);

  if (!hint) return null;

  return (
    <div className="ai-price-hint">
      <strong>🤖 {hint.verdict_label}</strong>
      <div className="ai-price-meta">
        <span>{hint.region_label}: ~{formatStars(hint.regional_avg_price)}</span>
        <span>{hint.season_name} ×{hint.season_factor.toFixed(2)}</span>
        <span>Расходники ~{formatStars(hint.ingredient_cost)}</span>
      </div>
      <p className="hint" style={{ margin: "6px 0 0" }}>
        Рекомендуем: <b>{formatStars(hint.suggested_price_min)} – {formatStars(hint.suggested_price_max)}</b>
        {" · "}
        мин. для повара {formatStars(hint.cook_minimum)} (маржа ~{hint.cook_margin_percent}%)
      </p>
      {hint.ingredient_items.length > 0 && (
        <p className="hint" style={{ margin: "4px 0 0", fontSize: 11 }}>
          {hint.ingredient_items.join(" · ")}
        </p>
      )}
      <p style={{ margin: "6px 0 0", fontSize: 13 }}>{hint.buyer_savings_hint}</p>
    </div>
  );
}
