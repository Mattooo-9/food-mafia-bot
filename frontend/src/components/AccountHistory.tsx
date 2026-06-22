import { useNavigate } from "react-router-dom";
import { formatPrice } from "../api";
import StatusBadge from "./StatusBadge";
import type { Order, SearchHistoryItem } from "../types";

interface Props {
  searches: SearchHistoryItem[];
  orders: Order[];
  onClearSearches: () => void;
  onPickSearch: (query: string) => void;
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function AccountHistory({ searches, orders, onClearSearches, onPickSearch }: Props) {
  const navigate = useNavigate();

  return (
    <>
      <h2 className="section-title">Мои запросы</h2>
      {searches.length === 0 ? (
        <div className="card hint-card">Поисковые запросы сохраняются здесь после нажатия «Найти»</div>
      ) : (
        <div className="card account-list">
          {searches.slice(0, 8).map((s) => (
            <button key={s.id} type="button" className="account-row" onClick={() => onPickSearch(s.query)}>
              <span className="account-row-main">🔍 {s.query}</span>
              <span className="account-row-meta">
                {s.results_count} · {formatWhen(s.created_at)}
              </span>
            </button>
          ))}
          <button type="button" className="btn small secondary" onClick={onClearSearches}>
            Очистить запросы
          </button>
        </div>
      )}

      <h2 className="section-title">Мои заказы</h2>
      {orders.length === 0 ? (
        <div className="card hint-card">Заказы появятся здесь после оформления</div>
      ) : (
        <div className="card account-list">
          {orders.slice(0, 5).map((o) => (
            <button key={o.id} type="button" className="account-row" onClick={() => navigate("/orders")}>
              <span className="account-row-main">{o.food_name}</span>
              <span className="account-row-meta">
                <StatusBadge status={o.status} /> · {formatPrice(o.total_price)}
              </span>
            </button>
          ))}
          <button type="button" className="btn small" onClick={() => navigate("/orders")}>
            Все заказы
          </button>
        </div>
      )}
    </>
  );
}
