import { useNavigate } from "react-router-dom";
import { formatDistance, formatPrice } from "../api";
import type { Food } from "../types";
import AppIcon from "./icons";

interface Props {
  food: Food;
  onToggleFavorite?: (food: Food) => void;
}

export default function FoodCard({ food, onToggleFavorite }: Props) {
  const navigate = useNavigate();
  return (
    <div className="card food-card" onClick={() => navigate(`/food/${food.id}`)}>
      {food.photo ? (
        <img className="food-photo" src={food.photo} alt={food.name} />
      ) : (
        <div className="food-photo food-photo-fallback">
          <AppIcon name="feed" size={32} />
        </div>
      )}
      <div className="food-info">
        <div className="row between">
          <div className="food-name">{food.name}</div>
          {onToggleFavorite && (
            <button
              className="icon-btn"
              aria-label={food.is_favorite ? "Убрать из избранного" : "В избранное"}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(food);
              }}
            >
              <AppIcon name={food.is_favorite ? "heart" : "heartOutline"} size={20} />
            </button>
          )}
        </div>
        <div className="food-meta">
          <span>{food.category.split(" › ").slice(-2).join(" › ")}</span>
          {food.distance_m != null && (
            <span className="meta-icon">
              <AppIcon name="distance" size={14} />
              {formatDistance(food.distance_m)}
            </span>
          )}
          <span className="meta-icon">
            <AppIcon name="time" size={14} />
            {food.cooking_time_minutes} мин
          </span>
        </div>
        <div className="food-meta">
          <span className="meta-icon">
            <AppIcon name="chef" size={14} />
            {food.cook_name ?? "Повар"}
          </span>
          {food.cook_rating > 0 && (
            <span className="meta-icon">
              <AppIcon name="star" size={14} />
              {food.cook_rating.toFixed(1)}
            </span>
          )}
        </div>
        <div className="row between">
          <div className="food-price">{formatPrice(food.price)}</div>
          <span className="hint">
            {food.portions > 0 ? `${food.portions} порц.` : "закончилось"}
          </span>
        </div>
      </div>
    </div>
  );
}
