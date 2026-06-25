import { useNavigate } from "react-router-dom";
import { formatPrice } from "../api";
import StatusBadge from "./StatusBadge";
import type { Order, SearchHistoryItem } from "../types";

interface Props {
  searches: SearchHistoryItem[];
  orders: Order[];
  onPickSearch: (query: string) => void;
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function AccountHistory({ searches, orders, onPickSearch }: Props) {
  const navigate = useNavigate();

  if (searches.length === 0 && orders.length === 0) {
    return null;
  }

  return (
    <>
      {searches.length > 0 && (
        <>
          <h2 className="section-title">Недавний поиск</h2>
          <div className="card account-list">
            {searches.slice(0, 6).map((s) => (
              <button key={s.id} type="button" className="account-row" onClick={() => onPickSearch(s.query)}>
                <span className="account-row-main">{s.query}</span>
                <span className="account-row-meta">
                  {s.results_count} · {formatWhen(s.created_at)}
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {orders.length > 0 && (
        <>
          <h2 className="section-title">Последние заказы</h2>
          <div className="card account-list">
            {orders.slice(0, 4).map((o) => (
              <button key={o.id} type="button" className="account-row" onClick={() => navigate("/orders")}>
                <span className="account-row-main">{o.food_name}</span>
                <span className="account-row-meta">
                  <StatusBadge status={o.status} /> · {formatPrice(o.total_price)}
                </span>
              </button>
            ))}
          </div>
        </>
      )}
    </>
  );
}
