import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, formatPrice } from "../api";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { haptic, showAlert } from "../telegram";
import type { Food, Order, OrderStatus } from "../types";

const NEXT_ACTIONS: Partial<Record<OrderStatus, { status: OrderStatus; label: string }[]>> = {
  NEW: [
    { status: "ACCEPTED", label: "✅ Принять" },
    { status: "CANCELLED", label: "❌ Отклонить" },
  ],
  ACCEPTED: [
    { status: "COOKING", label: "🍳 Готовлю" },
    { status: "CANCELLED", label: "❌ Отменить" },
  ],
  COOKING: [{ status: "READY", label: "🍱 Готово" }],
  READY: [{ status: "DELIVERED", label: "📦 Выдан" }],
};

export default function MyKitchenPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"orders" | "foods">("orders");
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

  const activeOrders = orders.filter((o) => !["DELIVERED", "CANCELLED"].includes(o.status));
  const pastOrders = orders.filter((o) => ["DELIVERED", "CANCELLED"].includes(o.status));

  return (
    <div className="page">
      <h1 className="page-title">Моя кухня 🧑‍🍳</h1>
      <div className="chips">
        <button className={`chip ${tab === "orders" ? "active" : ""}`} onClick={() => setTab("orders")}>
          📦 Заказы ({activeOrders.length})
        </button>
        <button className={`chip ${tab === "foods" ? "active" : ""}`} onClick={() => setTab("foods")}>
          🍲 Блюда ({foods.length})
        </button>
      </div>

      {tab === "orders" && (
        <>
          {activeOrders.length === 0 && (
            <div className="empty">
              <span className="emoji">📭</span>Активных заказов нет
            </div>
          )}
          {activeOrders.map((order) => (
            <div className="card" key={order.id}>
              <div className="row between">
                <strong>
                  #{order.id} · {order.food_name}
                </strong>
                <StatusBadge status={order.status} />
              </div>
              <div className="food-meta" style={{ marginTop: 6 }}>
                <span>× {order.quantity}</span>
                <span>👤 {order.buyer_name ?? "Покупатель"}</span>
                <span>{new Date(order.created_at).toLocaleString("ru-RU")}</span>
              </div>
              {order.comment && <p className="hint">💬 {order.comment}</p>}
              <div className="row between" style={{ marginTop: 8 }}>
                <span className="food-price">{formatPrice(order.total_price)}</span>
              </div>
              <div className="btn-row">
                {(NEXT_ACTIONS[order.status] ?? []).map((action) => (
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
            ➕ Добавить блюдо
          </button>
          <div style={{ height: 10 }} />
          {foods.length === 0 && (
            <div className="empty">
              <span className="emoji">🍳</span>Добавьте своё первое блюдо
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
                <span>🛒 заказов: {food.orders_count}</span>
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
                  ✏️ Изменить
                </button>
                <button className="btn small secondary" onClick={() => void toggleActive(food)}>
                  {food.is_active ? "🙈 Скрыть" : "👁 Показать"}
                </button>
                <button className="btn small danger" onClick={() => void removeFood(food)}>
                  🗑
                </button>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
