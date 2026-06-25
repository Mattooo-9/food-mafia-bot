import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="page">
      <div className="empty gloss-card" style={{ marginTop: 40 }}>
        <span className="emoji">🛸</span>
        <h2 style={{ margin: "8px 0" }}>Страница не найдена</h2>
        <p className="hint">Такого раздела нет</p>
        <Link to="/" className="btn" style={{ marginTop: 16, display: "inline-block", textDecoration: "none" }}>
          На главную
        </Link>
      </div>
    </div>
  );
}
