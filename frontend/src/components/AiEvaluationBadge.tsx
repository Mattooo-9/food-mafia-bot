import { useEffect, useState } from "react";
import { api, formatStars } from "../api";
import type { FoodEvaluation } from "../types";

interface Props {
  foodId: number;
}

export default function AiEvaluationBadge({ foodId }: Props) {
  const [ev, setEv] = useState<FoodEvaluation | null>(null);

  useEffect(() => {
    void api.getFoodEvaluation(foodId).then(setEv).catch(() => setEv(null));
  }, [foodId]);

  if (!ev) return null;

  const scoreClass =
    ev.overall_score >= 75 ? "high" : ev.overall_score >= 50 ? "mid" : "low";

  return (
    <div className="card ai-eval">
      <div className="row between">
        <strong>🤖 Оценка ИИ</strong>
        <span className={`ai-score-badge ${scoreClass}`}>{ev.overall_score}/100</span>
      </div>
      <div className="ai-meter-row">
        <span>Цена</span>
        <div className="ai-meter">
          <div className="ai-meter-fill" style={{ width: `${ev.price_score}%` }} />
        </div>
        <span>{ev.price_score}</span>
      </div>
      <div className="ai-meter-row">
        <span>Качество</span>
        <div className="ai-meter">
          <div className="ai-meter-fill" style={{ width: `${ev.quality_score}%` }} />
        </div>
        <span>{ev.quality_score}</span>
      </div>
      <div className="ai-meter-row">
        <span>Спрос</span>
        <div className="ai-meter">
          <div className="ai-meter-fill" style={{ width: `${ev.demand_score}%` }} />
        </div>
        <span>{ev.demand_score}</span>
      </div>
      <p className="hint" style={{ marginTop: 8 }}>
        {ev.verdict_label} · справедливо ~{formatStars(ev.fair_price)}
      </p>
      <p style={{ margin: "6px 0 0", fontSize: 14 }}>{ev.buyer_tip}</p>
    </div>
  );
}
