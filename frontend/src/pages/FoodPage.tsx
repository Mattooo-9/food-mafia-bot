import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError, formatDistance, formatPrice } from "../api";
import Spinner from "../components/Spinner";
import Stars from "../components/Stars";
import { PAYMENT_METHODS } from "../constants";
import { haptic, showAlert } from "../telegram";
import type { Food, PaymentMethod, Review } from "../types";

export default function FoodPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [food, setFood] = useState<Food | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [comment, setComment] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CASH");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    void (async () => {
      try {
        const foodData = await api.getFood(Number(id));
        setFood(foodData);
        const reviewsData = await api.getCookReviews(foodData.cook_id);
        setReviews(reviewsData.slice(0, 3));
      } catch {
        setFood(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <Spinner />;
  if (!food) {
    return (
      <div className="empty">
        <span className="emoji">😕</span>
        Блюдо не найдено
      </div>
    );
  }

  const order = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await api.createOrder(food.id, quantity, comment, paymentMethod);
      haptic("success");
      showAlert("Заказ оформлен! Расчёт — при получении.");
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
          <Stars rating={food.cook_rating} />
          <div className="food-meta">
            <span className={`badge ${food.cook_is_online ? "online" : "offline"}`}>
              {food.cook_is_online ? "онлайн" : "оффлайн"}
            </span>
          </div>
        </div>
      </div>

      {reviews.length > 0 && (
        <>
          <h2 className="section-title">Отзывы</h2>
          {reviews.map((review) => (
            <div className="card" key={review.id}>
              <div className="row between">
                <strong>{review.buyer_name ?? "Покупатель"}</strong>
                <span className="stars">{"★".repeat(review.rating)}</span>
              </div>
              {review.text && <p style={{ margin: "6px 0 0" }}>{review.text}</p>}
            </div>
          ))}
        </>
      )}

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
            <label>Способ оплаты</label>
            <div className="chips" style={{ paddingBottom: 0 }}>
              {PAYMENT_METHODS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className={`chip ${paymentMethod === m.id ? "active" : ""}`}
                  onClick={() => setPaymentMethod(m.id)}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Комментарий</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Время выдачи, пожелания"
              maxLength={512}
            />
          </div>

          <button className="btn" disabled={submitting} onClick={() => void order()}>
            {submitting ? "Оформляем..." : `Заказать · ${formatPrice(food.price * quantity)}`}
          </button>
          {error && <div className="error-text">{error}</div>}
        </div>
      )}
    </div>
  );
}
