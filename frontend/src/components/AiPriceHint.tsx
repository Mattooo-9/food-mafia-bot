import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { PriceSuggestion } from "../types";

interface Props {
  category: string;
  price: string;
  description: string;
  name: string;
  portions: string;
  autoFill?: boolean;
  onSuggest: (stars: number) => void;
}

export default function AiPriceHint({
  category,
  price,
  description,
  name,
  portions,
  autoFill = false,
  onSuggest,
}: Props) {
  const [hint, setHint] = useState<PriceSuggestion | null>(null);
  const autoDone = useRef(false);

  useEffect(() => {
    if (!category || name.trim().length < 2) {
      setHint(null);
      return;
    }
    const priceNum = Number(price);
    const timer = setTimeout(() => {
      void api
        .getPriceSuggestion(category, {
          price: priceNum > 0 ? priceNum : undefined,
          description,
          name,
          portions: Math.max(1, Number(portions) || 1),
        })
        .then((h) => {
          setHint(h);
          if (autoFill && !autoDone.current && priceNum <= 0 && h.recommended_price > 0) {
            autoDone.current = true;
            onSuggest(h.recommended_price);
          }
        })
        .catch(() => setHint(null));
    }, 500);
    return () => clearTimeout(timer);
  }, [category, price, description, name, portions, autoFill, onSuggest]);

  if (!hint) return null;

  return (
    <div className="ai-price-hint ai-price-simple">
      <p>{hint.simple_message || hint.summary}</p>
      {Number(price) !== hint.recommended_price && (
        <button type="button" className="btn small ai-apply-btn" onClick={() => onSuggest(hint.recommended_price)}>
          ✨ Поставить {hint.recommended_price} ⭐
        </button>
      )}
    </div>
  );
}
