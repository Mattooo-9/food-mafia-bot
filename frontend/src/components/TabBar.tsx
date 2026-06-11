import { NavLink } from "react-router-dom";

interface Props {
  isCook: boolean;
}

const tabClass = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");

export default function TabBar({ isCook }: Props) {
  return (
    <nav className="tabbar">
      <NavLink to="/" end className={tabClass}>
        <span className="tab-icon">🍲</span>Лента
      </NavLink>
      <NavLink to="/cooks" className={tabClass}>
        <span className="tab-icon">👨‍🍳</span>Повара
      </NavLink>
      <NavLink to="/orders" className={tabClass}>
        <span className="tab-icon">📦</span>Заказы
      </NavLink>
      <NavLink to="/favorites" className={tabClass}>
        <span className="tab-icon">❤️</span>Избранное
      </NavLink>
      {isCook && (
        <NavLink to="/my-kitchen" className={tabClass}>
          <span className="tab-icon">🧑‍🍳</span>Кухня
        </NavLink>
      )}
      <NavLink to="/profile" className={tabClass}>
        <span className="tab-icon">👤</span>Профиль
      </NavLink>
    </nav>
  );
}
