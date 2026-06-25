import { useNavigate } from "react-router-dom";
import { formatDistance } from "../api";
import type { Cook } from "../types";
import AppIcon from "./icons";
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
        <div className="cook-avatar food-photo-fallback">
          <AppIcon name="chef" size={32} />
        </div>
      )}
      <div className="food-info">
        <div className="row between">
          <div className="food-name">{name}</div>
          {onToggleFavorite && (
            <button
              className="icon-btn"
              aria-label={cook.is_favorite ? "Убрать из избранного" : "В избранное"}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(cook);
              }}
            >
              <AppIcon name={cook.is_favorite ? "heart" : "heartOutline"} size={20} />
            </button>
          )}
        </div>
        <div className="food-meta">
          <Stars rating={cook.rating_avg} count={cook.rating_count} />
        </div>
        <div className="food-meta">
          <span className={`badge ${cook.is_online ? "online" : "offline"}`}>
            {cook.is_online ? "онлайн" : "оффлайн"}
          </span>
          {cook.distance_m != null && (
            <span className="meta-icon">
              <AppIcon name="distance" size={14} />
              {formatDistance(cook.distance_m)}
            </span>
          )}
          {cook.is_subscribed && <span className="badge">подписка</span>}
        </div>
      </div>
    </div>
  );
}
