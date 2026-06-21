import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, formatPrice } from "../api";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { COOK_ORDER_ACTIONS, KITCHEN_TABS, ORDER_STATUS_RANK, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS } from "../constants";
import { haptic, showAlert } from "../telegram";
import type { Food, Order, OrderStatus } from "../types";

export default function MyKitchenPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<(typeof KITCHEN_TABS)[number]["id"]>("orders");
  const [foods, setFoods] = useState<Food[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [foodsData, ordersData] = await Promise.all([api.getMyFoods(), api.getCookOrders()]);
      setFoods(foodsData);
      setOrders(ordersData);
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
    await api.updateFood(food.id, { is_active: !food.is_active });
    await load();
  };

  const removeFood = async (food: Food) => {
    if (!window.confirm(`Удалить «${food.name}»?`)) return;
    await api.deleteFood(food.id);
    haptic("success");
    await load();
  };

  const changePortions = async (food: Food, delta: number) => {
    const next = Math.max(0, food.portions + delta);
    setFoods((prev) => prev.map((f) => (f.id === food.id ? { ...f, portions: next } : f)));
    await api.updateFood(food.id, { portions: next });
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
            {t.id === "orders" ? ` (${sortedActiveOrders.length})` : ` (${foods.length})`}
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
    </div>
  );
}
