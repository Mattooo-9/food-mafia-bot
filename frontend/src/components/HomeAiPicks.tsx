import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatPrice } from "../api";
import { haptic } from "../telegram";
import type { Recommendation } from "../types";

export default function HomeAiPicks() {
  const navigate = useNavigate();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void api
      .getAiRecommendations()
      .then((r) => setRecs(r.slice(0, 6)))
      .catch(() => setRecs([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="home-picks gloss-card">
        <div className="home-picks-head">
          <span>✨</span>
          <strong>ИИ подбирает…</strong>
        </div>
        <div className="home-picks-skeleton" />
      </div>
    );
  }

  if (recs.length === 0) return null;

  return (
    <section className="home-picks gloss-card">
      <div className="home-picks-head">
        <span>✨</span>
        <strong>ИИ рекомендует</strong>
      </div>
      <div className="home-picks-scroll">
        {recs.map((r) => (
          <button
            key={r.food_id}
            type="button"
            className="home-pick-card"
            onClick={() => {
              haptic();
              navigate(`/food/${r.food_id}`);
            }}
          >
            {r.food_photo ? (
              <img src={r.food_photo} alt="" className="home-pick-photo" />
            ) : (
              <div className="home-pick-photo">🍲</div>
            )}
            <div className="home-pick-body">
              <span className="home-pick-name">{r.food_name}</span>
              <span className="home-pick-meta">
                {formatPrice(r.price)}
                {r.distance_m != null && ` · ${Math.round(r.distance_m)} м`}
              </span>
              {r.buyer_tip && <span className="home-pick-tip">{r.buyer_tip}</span>}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
