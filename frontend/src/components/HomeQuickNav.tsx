import { useNavigate } from "react-router-dom";
import { haptic } from "../telegram";

const TILES = [
  { to: "/cooks", icon: "👨‍🍳", label: "Повара" },
  { to: "/orders", icon: "📋", label: "Заказы" },
  { to: "/favorites", icon: "❤️", label: "Избранное" },
  { to: "/profile", icon: "⚙️", label: "Профиль" },
] as const;

export default function HomeQuickNav() {
  const navigate = useNavigate();

  return (
    <div className="home-quick-nav">
      {TILES.map((tile) => (
        <button
          key={tile.to}
          type="button"
          className="home-quick-tile gloss-card"
          onClick={() => {
            haptic();
            navigate(tile.to);
          }}
        >
          <span className="home-quick-icon">{tile.icon}</span>
          <span>{tile.label}</span>
        </button>
      ))}
    </div>
  );
}
