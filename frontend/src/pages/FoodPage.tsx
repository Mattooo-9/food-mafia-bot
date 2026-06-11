import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError, formatDistance, formatPrice } from "../api";
import Spinner from "../components/Spinner";
import { haptic, showAlert } from "../telegram";
import type { Food } from "../types";

export default function FoodPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [food, setFood] = useState<Food | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .getFood(Number(id))
      .then(setFood)
      .catch(() => setFood(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spinner />;
  if (!food) {
    return (
      <div className="empty">
        <span className="emoji">😕</span>Блюдо не найдено
      </div>
    );
  }

  const order = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await api.createOrder(food.id, quantity, comment);
      haptic("success");
      showAlert("Заказ оформлен! Повар получит уведомление.");
      navigate("/orders");
    } catch (e) {
      haptic("error");
      setError(e instanceof ApiError ? e.message : "Не удалось оформить заказ");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleFavorite = async () => {
    haptic();
    if (food.is_favorite) {
      await api.removeFavoriteFood(food.id);
    } else {
      await api.addFavoriteFood(food.id);
    }
    setFood({ ...food, is_favorite: !food.is_favorite });
  };

  const maxQty = Math.max(food.portions, 0);

  return (
    <div className="page">
      {food.photo ? (
        <img className="detail-photo" src={food.photo} alt={food.name} />
      ) : (
        <div className="detail-photo">🍲</div>
      )}

      <div className="card" style={{ marginTop: 12 }}>
        <div className="row between">
          <h1 className="page-title" style={{ margin: 0 }}>
            {food.name}
          </h1>
          <button className="icon-btn" onClick={() => void toggleFavorite()}>
            {food.is_favorite ? "❤️" : "🤍"}
          </button>
        </div>
        <div className="food-meta" style={{ marginTop: 8 }}>
          <span className="badge">{food.category}</span>
          <span>⏱ {food.cooking_time_minutes} мин</span>
          {food.distance_m != null && <span>📍 {formatDistance(food.distance_m)}</span>}
        </div>
        {food.description && <p>{food.description}</p>}
        <div className="food-price" style={{ fontSize: 22 }}>
          {formatPrice(food.price)}
        </div>
        <p className="hint">
          {food.portions > 0 ? `Доступно порций: ${food.portions}` : "Порции закончились"}
        </p>
      </div>

      <div
        className="card food-card"
        onClick={() => navigate(`/cook/${food.cook_id}`)}
        style={{ cursor: "pointer" }}
      >
        <div className="cook-avatar">👨‍🍳</div>
        <div className="food-info">
          <div className="food-name">{food.cook_name ?? "Повар"}</div>
          <div className="food-meta">
            {food.cook_rating > 0 && <span>⭐ {food.cook_rating.toFixed(1)}</span>}
            <span className={`badge ${food.cook_is_online ? "online" : "offline"}`}>
              {food.cook_is_online ? "● онлайн" : "○ оффлайн"}
            </span>
          </div>
          <span className="hint">Открыть профиль повара →</span>
        </div>
      </div>

      {maxQty > 0 && (
        <div className="card">
          <div className="row between">
            <strong>Количество</strong>
            <div className="qty-control">
              <button onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
              <span>{quantity}</span>
              <button onClick={() => setQuantity((q) => Math.min(maxQty, q + 1))}>+</button>
            </div>
          </div>
          <div className="field" style={{ marginTop: 12 }}>
            <label>Комментарий к заказу</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Например: без лука, заберу в 18:00"
              maxLength={512}
            />
          </div>
          <button className="btn" disabled={submitting} onClick={() => void order()}>
            {submitting ? "Оформляем..." : `Заказать за ${formatPrice(food.price * quantity)}`}
          </button>
          {error && <div className="error-text">{error}</div>}
        </div>
      )}
    </div>
  );
}
