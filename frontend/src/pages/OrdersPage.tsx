import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError, formatPrice } from "../api";
import OrderWishForm from "../components/OrderWishForm";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { ORDER_STATUS_RANK, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, WISH_STATUS_LABELS } from "../constants";
import { haptic, showAlert } from "../telegram";
import type { Order, OrderWish } from "../types";

function ReviewForm({ order, onDone }: { order: Order; onDone: () => void }) {
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      await api.createReview(order.id, rating, text);
      haptic("success");
      onDone();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось отправить отзыв");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ marginTop: 10 }}>
      <div className="row" style={{ marginBottom: 8 }}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            className="icon-btn"
            style={{ opacity: star <= rating ? 1 : 0.3 }}
            onClick={() => setRating(star)}
          >
            ⭐
          </button>
        ))}
      </div>
      <div className="field">
        <textarea
          placeholder="Ваш отзыв (необязательно)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={1000}
        />
      </div>
      <button className="btn small" disabled={submitting} onClick={() => void submit()}>
        Отправить отзыв
      </button>
    </div>
  );
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [wishes, setWishes] = useState<OrderWish[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewFor, setReviewFor] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ords, wishList] = await Promise.all([api.getMyOrders(), api.getMyWishes()]);
      setOrders(ords);
      setWishes(wishList);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const sortedOrders = useMemo(
    () =>
      [...orders].sort((a, b) => {
        const rank = ORDER_STATUS_RANK[a.status] - ORDER_STATUS_RANK[b.status];
        if (rank !== 0) return rank;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }),
    [orders],
  );

  const cancelWish = async (wish: OrderWish) => {
    try {
      await api.cancelWish(wish.id);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось отменить запрос");
    }
  };

  const cancel = async (order: Order) => {
    try {
      await api.cancelOrder(order.id);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось отменить заказ");
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="page">
      <h1 className="page-title">Заказы</h1>

      <OrderWishForm onCreated={() => void load()} />

      {wishes.filter((w) => w.status !== "CANCELLED").length > 0 && (
        <>
          <h2 className="section-title">Мои запросы</h2>
          {wishes
            .filter((w) => w.status !== "CANCELLED")
            .map((wish) => (
              <div className="card" key={wish.id}>
                <div className="row between">
                  <strong>{wish.title}</strong>
                  <span className="hint">{WISH_STATUS_LABELS[wish.status] ?? wish.status}</span>
                  {wish.cook_name && wish.status !== "OPEN" && (
                    <span className="hint"> · {wish.cook_name}</span>
                  )}
                </div>
                {wish.details && <p className="hint">💬 {wish.details}</p>}
                {wish.status === "OPEN" && (
                  <button
                    className="btn small danger"
                    onClick={() => void cancelWish(wish)}
                  >
                    Отменить
                  </button>
                )}
              </div>
            ))}
        </>
      )}

      {orders.length === 0 ? (
        <div className="empty">
          <span className="emoji">🛒</span>Вы ещё ничего не заказывали
        </div>
      ) : (
        sortedOrders.map((order) => (
          <div className="card" key={order.id}>
            <div className="row between">
              <strong>
                #{order.id} · {order.food_name}
              </strong>
              <StatusBadge status={order.status} />
            </div>
            <div className="food-meta" style={{ marginTop: 6 }}>
              <span>× {order.quantity}</span>
              <span>{order.cook_name ?? "Повар"}</span>
              <span>{PAYMENT_METHOD_LABELS[order.payment_method]}</span>
              <span>{PAYMENT_STATUS_LABELS[order.payment_status]}</span>
              {order.referral_discount > 0 && (
                <span>−{formatPrice(order.referral_discount)} с баланса</span>
              )}
              <span>{new Date(order.created_at).toLocaleString("ru-RU")}</span>
            </div>
            <div className="row between" style={{ marginTop: 8 }}>
              <span className="food-price">{formatPrice(order.total_price)}</span>
              <div className="row">
                {order.status === "NEW" && (
                  <button className="btn small danger" onClick={() => void cancel(order)}>
                    Отменить
                  </button>
                )}
                {order.status === "DELIVERED" && !order.has_review && (
                  <button
                    className="btn small secondary"
                    onClick={() => setReviewFor(reviewFor === order.id ? null : order.id)}
                  >
                    ⭐ Оценить
                  </button>
                )}
                {order.has_review && <span className="hint">✓ отзыв оставлен</span>}
              </div>
            </div>
            {reviewFor === order.id && (
              <ReviewForm
                order={order}
                onDone={() => {
                  setReviewFor(null);
                  void load();
                }}
              />
            )}
          </div>
        ))
      )}
    </div>
  );
}
