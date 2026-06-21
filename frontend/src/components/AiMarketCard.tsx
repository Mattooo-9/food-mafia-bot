import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatStars } from "../api";
import type { MarketOverview, Recommendation } from "../types";

export default function AiMarketCard() {
  const navigate = useNavigate();
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const [m, r] = await Promise.all([api.getAiMarket(), api.getAiRecommendations()]);
        setMarket(m);
        setRecs(r.slice(0, 3));
      } catch {
        setMarket(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return null;
  if (!market || market.total_dishes === 0) return null;

  const topInsight = market.insights[0];

  return (
    <div className="card ai-card">
      <div className="ai-glow" />
      <div className="row between">
        <strong className="ai-title">🤖 ИИ-аналитик рынка</strong>
        <span className="badge online">live</span>
      </div>
      <p className="hint ai-desc">{market.analyst_note}</p>
      <div className="ai-stats">
        <span>
          Блюд рядом <strong>{market.total_dishes}</strong>
        </span>
        <span>
          Медиана <strong>{formatStars(market.median_price)}</strong>
        </span>
        <span>
          Топ категория <strong>{market.top_category}</strong>
        </span>
      </div>
      {topInsight && (
        <p className="ai-insight">{topInsight.summary}</p>
      )}
      {recs.length > 0 && (
        <>
          <p className="hint" style={{ margin: "10px 0 6px", fontSize: 12 }}>
            Рекомендует для вас
          </p>
          <div className="ai-recs">
            {recs.map((r) => (
              <button
                key={r.food_id}
                type="button"
                className="ai-rec-chip"
                onClick={() => navigate(`/food/${r.food_id}`)}
              >
                <span>{r.food_name}</span>
                <span className="ai-score">{r.overall_score}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
