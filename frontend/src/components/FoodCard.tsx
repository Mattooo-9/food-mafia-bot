import { useNavigate } from "react-router-dom";
import { formatDistance, formatPrice } from "../api";
import type { Food } from "../types";

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
        <div className="food-photo">🍲</div>
      )}
      <div className="food-info">
        <div className="row between">
          <div className="food-name">{food.name}</div>
          {onToggleFavorite && (
            <button
              className="icon-btn"
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(food);
              }}
            >
              {food.is_favorite ? "❤️" : "🤍"}
            </button>
          )}
        </div>
        <div className="food-meta">
          <span>{food.category}</span>
          {food.distance_m != null && <span>📍 {formatDistance(food.distance_m)}</span>}
          <span>⏱ {food.cooking_time_minutes} мин</span>
        </div>
        <div className="food-meta">
          <span>👨‍🍳 {food.cook_name ?? "Повар"}</span>
          {food.cook_rating > 0 && <span>⭐ {food.cook_rating.toFixed(1)}</span>}
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
