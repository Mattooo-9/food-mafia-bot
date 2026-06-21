import { useEffect, useState } from "react";
import { api, formatStars } from "../api";
import type { PriceSuggestion } from "../types";

interface Props {
  category: string;
  price: string;
}

export default function AiPriceHint({ category, price }: Props) {
  const [hint, setHint] = useState<PriceSuggestion | null>(null);

  useEffect(() => {
    if (!category) return;
    const priceNum = Number(price);
    const timer = setTimeout(() => {
      void api
        .getPriceSuggestion(category, priceNum > 0 ? priceNum : undefined)
        .then(setHint)
        .catch(() => setHint(null));
    }, 400);
    return () => clearTimeout(timer);
  }, [category, price]);

  if (!hint) return null;

  return (
    <div className="ai-price-hint">
      <strong>🤖 {hint.verdict_label}</strong>
      <p className="hint" style={{ margin: "4px 0 0" }}>
        Рекомендуем: {formatStars(hint.suggested_price_min)} – {formatStars(hint.suggested_price_max)}
        {" · "}
        {hint.summary}
      </p>
    </div>
  );
}
