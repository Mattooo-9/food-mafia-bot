import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Recommendation } from "../types";

export default function AiMarketCard() {
  const navigate = useNavigate();
  const [recs, setRecs] = useState<Recommendation[]>([]);

  useEffect(() => {
    void api.getAiRecommendations().then((r) => setRecs(r.slice(0, 4))).catch(() => setRecs([]));
  }, []);

  if (recs.length === 0) return null;

  return (
    <div className="card ai-card ai-card-simple">
      <strong className="ai-title">✨ ИИ подобрал для вас</strong>
      <div className="ai-recs" style={{ marginTop: 10 }}>
        {recs.map((r) => (
          <button
            key={r.food_id}
            type="button"
            className="ai-rec-chip"
            onClick={() => navigate(`/food/${r.food_id}`)}
          >
            {r.food_name}
          </button>
        ))}
      </div>
    </div>
  );
}
