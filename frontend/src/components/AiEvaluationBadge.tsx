import { useEffect, useState } from "react";
import { api } from "../api";
import type { FoodEvaluation } from "../types";

interface Props {
  foodId: number;
}

const ICONS: Record<string, string> = {
  fair: "✅",
  underpriced: "🔥",
  premium: "👍",
  overpriced: "⚠️",
  below_cost: "⚠️",
};

export default function AiEvaluationBadge({ foodId }: Props) {
  const [ev, setEv] = useState<FoodEvaluation | null>(null);

  useEffect(() => {
    void api.getFoodEvaluation(foodId).then(setEv).catch(() => setEv(null));
  }, [foodId]);

  if (!ev) return null;

  const tip = ev.simple_tip || ev.buyer_tip;
  const icon = ICONS[ev.verdict] ?? "🤖";

  return (
    <div className="card ai-eval ai-eval-simple">
      <p>
        {icon} <strong>{tip}</strong>
      </p>
    </div>
  );
}
