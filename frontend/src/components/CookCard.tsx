import { useNavigate } from "react-router-dom";
import { formatDistance } from "../api";
import type { Cook } from "../types";
import Stars from "./Stars";

interface Props {
  cook: Cook;
  onToggleFavorite?: (cook: Cook) => void;
}

export default function CookCard({ cook, onToggleFavorite }: Props) {
  const navigate = useNavigate();
  const name = cook.cook_name ?? cook.first_name ?? "Повар";
  return (
    <div className="card food-card" onClick={() => navigate(`/cook/${cook.id}`)}>
      {cook.cook_photo ? (
        <img className="cook-avatar" src={cook.cook_photo} alt={name} />
      ) : (
        <div className="cook-avatar">👨‍🍳</div>
      )}
      <div className="food-info">
        <div className="row between">
          <div className="food-name">{name}</div>
          {onToggleFavorite && (
            <button
              className="icon-btn"
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(cook);
              }}
            >
              {cook.is_favorite ? "❤️" : "🤍"}
            </button>
          )}
        </div>
        <div className="food-meta">
          <Stars rating={cook.rating_avg} count={cook.rating_count} />
        </div>
        <div className="food-meta">
          <span className={`badge ${cook.is_online ? "online" : "offline"}`}>
            {cook.is_online ? "● онлайн" : "○ оффлайн"}
          </span>
          {cook.distance_m != null && <span>📍 {formatDistance(cook.distance_m)}</span>}
          {cook.is_subscribed && <span className="badge">🔔 подписка</span>}
        </div>
      </div>
    </div>
  );
}
