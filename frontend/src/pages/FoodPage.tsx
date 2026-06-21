import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTonConnectUI, useTonWallet } from "@tonconnect/ui-react";
import {
  api,
  ApiError,
  calcReferralDiscount,
  formatDistance,
  formatStars,
  formatTon,
} from "../api";
import Spinner from "../components/Spinner";
import Stars from "../components/Stars";
import { PAYMENT_METHODS } from "../constants";
import { haptic, openInvoice, showAlert } from "../telegram";
import type { Food, PaymentMethod, ReferralInfo, Review, TonPayment } from "../types";
import { useUser } from "../UserContext";

export default function FoodPage() {
  const { user, refresh } = useUser();
  const { id } = useParams();
  const navigate = useNavigate();
  const [tonConnectUI] = useTonConnectUI();
  const tonWallet = useTonWallet();
  const [food, setFood] = useState<Food | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [comment, setComment] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("STARS");
  const [tonPerStar, setTonPerStar] = useState(0.004);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referral, setReferral] = useState<ReferralInfo | null>(null);

  useEffect(() => {
    void api.getReferral().then(setReferral).catch(() => setReferral(null));
    void api.getCurrency().then((c) => setTonPerStar(c.ton_per_star)).catch(() => undefined);
  }, []);

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

  const payWithTon = async (orderId: number, tonPayment: TonPayment) => {
    const nanoTon = Math.ceil(tonPayment.amount_ton * 1e9);
    await tonConnectUI.sendTransaction({
      validUntil: Math.floor(Date.now() / 1000) + 600,
      messages: [
        {
          address: tonPayment.wallet_address,
          amount: String(nanoTon),
        },
      ],
    });
    await api.confirmTonPayment(orderId);
  };

  const order = async () => {
    setSubmitting(true);
    setError(null);
    try {
      if (paymentMethod === "TON" && !tonWallet) {
        await tonConnectUI.openModal();
        setError("Подключите TON-кошелёк для оплаты");
        setSubmitting(false);
        return;
      }

      const created = await api.createOrder(food.id, quantity, comment, paymentMethod);

      if (paymentMethod === "STARS" && created.invoice_link) {
        openInvoice(created.invoice_link, async (status) => {
          if (status === "paid") {
            haptic("success");
            await refresh();
            showAlert("Оплачено! Повар получил заказ.");
            navigate("/orders");
          } else if (status === "failed" || status === "cancelled") {
            haptic("error");
            try {
              await api.cancelOrder(created.id);
            } catch {
              // ignore
            }
            setError("Оплата отменена");
            setSubmitting(false);
          }
        });
        return;
      }

      if (paymentMethod === "TON" && created.ton_payment) {
        await payWithTon(created.id, created.ton_payment);
        haptic("success");
        await refresh();
        showAlert("TON отправлен! Повар получил заказ.");
        navigate("/orders");
        return;
      }

      haptic("error");
      setError("Не удалось подготовить оплату");
    } catch (e) {
      haptic("error");
      setError(e instanceof ApiError ? e.message : "Не удалось оформить заказ");
    } finally {
      if (paymentMethod !== "STARS") {
        setSubmitting(false);
      }
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
  const gross = Math.round(food.price * quantity * 100) / 100;
  const maxDiscountPercent = referral?.max_discount_percent ?? 15;
  const balance = user?.referral_balance ?? referral?.balance ?? 0;
  const referralDiscount = calcReferralDiscount(balance, gross, maxDiscountPercent);
  const total = Math.round((gross - referralDiscount) * 100) / 100;
  const tonEstimate = Math.round(total * tonPerStar * 1e6) / 1e6;

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
          {formatStars(food.price)}
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
              {PAYMENT_METHODS.map((m) => {
                const disabled = m.id === "TON" && !food.cook_accepts_ton;
                return (
                  <button
                    key={m.id}
                    type="button"
                    className={`chip ${paymentMethod === m.id ? "active" : ""}`}
                    disabled={disabled}
                    onClick={() => setPaymentMethod(m.id)}
                    title={disabled ? "Повар ещё не подключил TON-кошелёк" : undefined}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>
            {paymentMethod === "TON" && (
              <p className="hint" style={{ marginTop: 8 }}>
                ≈ {formatTon(tonEstimate)} · оплата через ваш TON-кошелёк
              </p>
            )}
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
            {submitting ? "Оформляем..." : `Заказать · ${formatStars(total)}`}
          </button>
          {referralDiscount > 0 && (
            <p className="hint" style={{ marginTop: 8, textAlign: "center" }}>
              С баланса: −{formatStars(referralDiscount)}
            </p>
          )}
          {error && <div className="error-text">{error}</div>}
        </div>
      )}
    </div>
  );
}
