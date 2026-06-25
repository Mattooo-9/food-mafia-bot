import type { UserInsights } from "../types";
import LocationBar from "./LocationBar";

interface HeaderProps {
  name: string;
}

export default function HomeHeader({ name }: HeaderProps) {
  return (
    <header className="home-header gloss-card">
      <div className="home-header-main">
        <p className="home-greet">{name}</p>
        <h1 className="home-title">Еда Рядом</h1>
      </div>
      <LocationBar compact />
    </header>
  );
}

interface InsightProps {
  insights: UserInsights;
  onOrders: () => void;
}

export function HomeInsight({ insights, onOrders }: InsightProps) {
  const hasActivity =
    insights.active_orders > 0 || insights.open_wishes > 0 || insights.claimed_wishes > 0;

  return (
    <section className="home-insight gloss-card">
      {insights.summary && <p className="home-insight-text">{insights.summary}</p>}
      {hasActivity && (
        <button type="button" className="home-insight-cta" onClick={onOrders}>
          {insights.active_orders > 0 && `${insights.active_orders} заказ`}
          {insights.active_orders > 0 && insights.open_wishes > 0 && " · "}
          {insights.open_wishes > 0 && `${insights.open_wishes} запрос`}
          {insights.claimed_wishes > 0 && !insights.open_wishes && `${insights.claimed_wishes} в работе`}
          {" →"}
        </button>
      )}
      {!insights.has_location && (
        <p className="home-insight-warn">Включите гео — ИИ точнее подберёт рядом</p>
      )}
    </section>
  );
}
