import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, formatDistance } from "../api";
import FoodCard from "../components/FoodCard";
import Spinner from "../components/Spinner";
import Stars from "../components/Stars";
import { haptic } from "../telegram";
import type { Cook, Food, Review } from "../types";

export default function CookPage() {
  const { id } = useParams();
  const cookId = Number(id);
  const [cook, setCook] = useState<Cook | null>(null);
  const [foods, setFoods] = useState<Food[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [cookData, foodsData, reviewsData] = await Promise.all([
        api.getCook(cookId),
        api.getCookFoods(cookId),
        api.getCookReviews(cookId),
      ]);
      setCook(cookData);
      setFoods(foodsData);
      setReviews(reviewsData);
    } catch {
      setCook(null);
    } finally {
      setLoading(false);
    }
  }, [cookId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <Spinner />;
  if (!cook) {
    return (
      <div className="empty">
        <span className="emoji">😕</span>Повар не найден
      </div>
    );
  }

  const name = cook.cook_name ?? cook.first_name ?? "Повар";

  const toggleFavorite = async () => {
    haptic();
    if (cook.is_favorite) {
      await api.removeFavoriteCook(cook.id);
    } else {
      await api.addFavoriteCook(cook.id);
    }
    setCook({ ...cook, is_favorite: !cook.is_favorite });
  };

  const toggleSubscription = async () => {
    haptic();
    if (cook.is_subscribed) {
      await api.unsubscribe(cook.id);
    } else {
      await api.subscribe(cook.id);
    }
    setCook({ ...cook, is_subscribed: !cook.is_subscribed });
  };

  const toggleFoodFavorite = async (food: Food) => {
    haptic();
    if (food.is_favorite) {
      await api.removeFavoriteFood(food.id);
    } else {
      await api.addFavoriteFood(food.id);
    }
    setFoods((prev) =>
      prev.map((f) => (f.id === food.id ? { ...f, is_favorite: !f.is_favorite } : f)),
    );
  };

  return (
    <div className="page">
      <div className="card food-card">
        {cook.cook_photo ? (
          <img className="cook-avatar" src={cook.cook_photo} alt={name} />
        ) : (
          <div className="cook-avatar">👨‍🍳</div>
        )}
        <div className="food-info">
          <div className="row between">
            <div className="food-name">{name}</div>
            <button className="icon-btn" onClick={() => void toggleFavorite()}>
              {cook.is_favorite ? "❤️" : "🤍"}
            </button>
          </div>
          <Stars rating={cook.rating_avg} count={cook.rating_count} />
          <div className="food-meta">
            <span className={`badge ${cook.is_online ? "online" : "offline"}`}>
              {cook.is_online ? "● онлайн" : "○ оффлайн"}
            </span>
            {cook.distance_m != null && <span>📍 {formatDistance(cook.distance_m)}</span>}
          </div>
        </div>
      </div>

      {cook.cook_description && <div className="card">{cook.cook_description}</div>}

      <button className={`btn ${cook.is_subscribed ? "secondary" : ""}`} onClick={() => void toggleSubscription()}>
        {cook.is_subscribed ? "🔕 Отписаться от новых блюд" : "🔔 Подписаться на новые блюда"}
      </button>

      <h2 className="section-title">Блюда ({foods.length})</h2>
      {foods.length === 0 ? (
        <div className="empty">Пока нет активных блюд</div>
      ) : (
        foods.map((food) => (
          <FoodCard key={food.id} food={food} onToggleFavorite={toggleFoodFavorite} />
        ))
      )}

      <h2 className="section-title">Отзывы ({reviews.length})</h2>
      {reviews.length === 0 ? (
        <div className="empty">Отзывов пока нет</div>
      ) : (
        reviews.map((review) => (
          <div className="card" key={review.id}>
            <div className="row between">
              <strong>{review.buyer_name ?? "Покупатель"}</strong>
              <span className="stars">{"★".repeat(review.rating)}</span>
            </div>
            {review.text && <p style={{ margin: "6px 0 0" }}>{review.text}</p>}
            <span className="hint">{new Date(review.created_at).toLocaleDateString("ru-RU")}</span>
          </div>
        ))
      )}
    </div>
  );
}
