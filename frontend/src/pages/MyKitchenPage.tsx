import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, formatPrice, formatDistance } from "../api";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { COOK_ORDER_ACTIONS, KITCHEN_TABS, ORDER_STATUS_RANK, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, WISH_STATUS_LABELS } from "../constants";
import { haptic, showAlert } from "../telegram";
import type { Food, Order, OrderStatus, OrderWish } from "../types";

export default function MyKitchenPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<(typeof KITCHEN_TABS)[number]["id"]>("orders");
  const [foods, setFoods] = useState<Food[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [wishes, setWishes] = useState<OrderWish[]>([]);
  const [myWishes, setMyWishes] = useState<OrderWish[]>([]);
  const [recipeHints, setRecipeHints] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [foodsData, ordersData, wishesData, myWishesData, hintsData] = await Promise.all([
        api.getMyFoods(),
        api.getCookOrders(),
        api.getCookWishes(),
        api.getCookMyWishes(),
        api.getRecipeHints(),
      ]);
      setFoods(foodsData);
      setOrders(ordersData);
      setWishes(wishesData);
      setMyWishes(myWishesData);
      setRecipeHints(hintsData.hints);
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось загрузить кухню");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const sortedActiveOrders = useMemo(() => {
    const active = orders.filter((o) => !["DELIVERED", "CANCELLED"].includes(o.status));
    return [...active].sort((a, b) => {
      const rank = ORDER_STATUS_RANK[a.status] - ORDER_STATUS_RANK[b.status];
      if (rank !== 0) return rank;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [orders]);

  const pastOrders = useMemo(
    () =>
      orders
        .filter((o) => ["DELIVERED", "CANCELLED"].includes(o.status))
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [orders],
  );

  const openWishes = useMemo(() => wishes.filter((w) => w.status === "OPEN"), [wishes]);

  const changeStatus = async (order: Order, status: OrderStatus) => {
    try {
      await api.changeOrderStatus(order.id, status);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось изменить статус");
    }
  };

  const toggleActive = async (food: Food) => {
    haptic();
    try {
      await api.updateFood(food.id, { is_active: !food.is_active });
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось изменить статус");
    }
  };

  const removeFood = async (food: Food) => {
    if (!window.confirm(`Удалить «${food.name}»?`)) return;
    try {
      await api.deleteFood(food.id);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось удалить");
    }
  };

  const changePortions = async (food: Food, delta: number) => {
    const next = Math.max(0, food.portions + delta);
    setFoods((prev) => prev.map((f) => (f.id === food.id ? { ...f, portions: next } : f)));
    try {
      await api.updateFood(food.id, { portions: next });
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось обновить порции");
      await load();
    }
  };

  const claimWish = async (wish: OrderWish) => {
    try {
      await api.claimWish(wish.id);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось взять заказ");
    }
  };

  const completeWish = async (wish: OrderWish) => {
    try {
      await api.completeWish(wish.id);
      haptic("success");
      await load();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось завершить");
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="page">
      <h1 className="page-title">Моя кухня</h1>
      <div className="chips">
        {KITCHEN_TABS.map((t) => (
          <button
            key={t.id}
            className={`chip ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id === "orders"
              ? ` (${sortedActiveOrders.length})`
              : t.id === "wishes"
                ? ` (${openWishes.length + myWishes.length})`
                : ` (${foods.length})`}
          </button>
        ))}
      </div>

      {tab === "orders" && (
        <>
          {sortedActiveOrders.length === 0 && (
            <div className="empty">
              <span className="emoji">📭</span>
              Активных заказов нет
            </div>
          )}
          {sortedActiveOrders.map((order) => (
            <div className="card" key={order.id}>
              <div className="row between">
                <strong>
                  #{order.id} · {order.food_name}
                </strong>
                <StatusBadge status={order.status} />
              </div>
              <div className="food-meta" style={{ marginTop: 6 }}>
                <span>× {order.quantity}</span>
                <span>{order.buyer_name ?? "Покупатель"}</span>
                <span>{PAYMENT_METHOD_LABELS[order.payment_method]}</span>
                <span>{PAYMENT_STATUS_LABELS[order.payment_status]}</span>
                <span>{new Date(order.created_at).toLocaleString("ru-RU")}</span>
              </div>
              {order.comment && <p className="hint">💬 {order.comment}</p>}
              <div className="row between" style={{ marginTop: 8 }}>
                <span className="food-price">{formatPrice(order.total_price)}</span>
              </div>
              <div className="btn-row">
                {(COOK_ORDER_ACTIONS[order.status] ?? []).map((action) => (
                  <button
                    key={action.status}
                    className={`btn small ${action.status === "CANCELLED" ? "danger" : ""}`}
                    onClick={() => void changeStatus(order, action.status)}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ))}

          {pastOrders.length > 0 && (
            <>
              <h2 className="section-title">История</h2>
              {pastOrders.map((order) => (
                <div className="card" key={order.id}>
                  <div className="row between">
                    <span>
                      #{order.id} · {order.food_name} × {order.quantity}
                    </span>
                    <StatusBadge status={order.status} />
                  </div>
                  <div className="row between" style={{ marginTop: 4 }}>
                    <span className="hint">{new Date(order.created_at).toLocaleString("ru-RU")}</span>
                    <span className="food-price">{formatPrice(order.total_price)}</span>
                  </div>
                </div>
              ))}
            </>
          )}
        </>
      )}

      {tab === "foods" && (
        <>
          {recipeHints.length > 0 && (
            <div className="card recipe-hints">
              <strong>💡 Идеи по теме</strong>
              <ul>
                {recipeHints.map((h) => (
                  <li key={h}>{h}</li>
                ))}
              </ul>
            </div>
          )}
          <button className="btn" onClick={() => navigate("/my-kitchen/dish/new")}>
            Добавить блюдо
          </button>
          <div style={{ height: 10 }} />
          {foods.length === 0 && (
            <div className="empty">
              <span className="emoji">🍳</span>
              Добавьте своё первое блюдо
            </div>
          )}
          {foods.map((food) => (
            <div className="card" key={food.id}>
              <div className="row between">
                <strong>{food.name}</strong>
                <span className={`badge ${food.is_active ? "online" : "offline"}`}>
                  {food.is_active ? "активно" : "скрыто"}
                </span>
              </div>
              <div className="food-meta" style={{ marginTop: 6 }}>
                <span>{food.category}</span>
                <span>{formatPrice(food.price)}</span>
                <span>заказов: {food.orders_count}</span>
              </div>
              <div className="row between" style={{ marginTop: 10 }}>
                <span>Порции:</span>
                <div className="qty-control">
                  <button onClick={() => void changePortions(food, -1)}>−</button>
                  <span>{food.portions}</span>
                  <button onClick={() => void changePortions(food, 1)}>+</button>
                </div>
              </div>
              <div className="btn-row">
                <button className="btn small secondary" onClick={() => navigate(`/my-kitchen/dish/${food.id}`)}>
                  Изменить
                </button>
                <button className="btn small secondary" onClick={() => void toggleActive(food)}>
                  {food.is_active ? "Скрыть" : "Показать"}
                </button>
                <button className="btn small danger" onClick={() => void removeFood(food)}>
                  Удалить
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      {tab === "wishes" && (
        <>
          {myWishes.length > 0 && (
            <>
              <h2 className="section-title">Мои в работе</h2>
              {myWishes.map((wish) => (
                <div className="card gloss-card" key={`mine-${wish.id}`}>
                  <div className="row between">
                    <strong>{wish.title}</strong>
                    <span className="badge online">{WISH_STATUS_LABELS.CLAIMED}</span>
                  </div>
                  <div className="food-meta" style={{ marginTop: 6 }}>
                    <span>× {wish.portions}</span>
                    <span>{wish.buyer_name ?? "Покупатель"}</span>
                  </div>
                  {wish.details && <p className="hint">💬 {wish.details}</p>}
                  <button className="btn small" onClick={() => void completeWish(wish)}>
                    Выполнено
                  </button>
                </div>
              ))}
            </>
          )}
          <h2 className="section-title">Открытые запросы</h2>
          {openWishes.length === 0 && (
            <div className="empty">
              <span className="emoji">📋</span>
              Пока нет открытых запросов от покупателей
            </div>
          )}
          {openWishes.map((wish) => (
            <div className="card" key={wish.id}>
              <div className="row between">
                <strong>{wish.title}</strong>
                <span className="badge online">открыт</span>
              </div>
              <div className="food-meta" style={{ marginTop: 6 }}>
                <span>× {wish.portions}</span>
                <span>{wish.buyer_name ?? "Покупатель"}</span>
                {wish.budget_max != null && <span>до {formatPrice(wish.budget_max)}</span>}
                {wish.distance_m != null && <span>{formatDistance(wish.distance_m)}</span>}
              </div>
              {wish.details && <p className="hint">💬 {wish.details}</p>}
              <button className="btn small" onClick={() => void claimWish(wish)}>
                Взять заказ
              </button>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
