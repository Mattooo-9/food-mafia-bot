import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";

interface Props {
  compact?: boolean;
}

export default function LocationBar({ compact = false }: Props) {
  const { user, requestLocation } = useUser();
  const hasLocation = user?.lat != null && user?.lon != null;

  const update = async () => {
    const ok = await requestLocation();
    haptic(ok ? "success" : "error");
    if (!ok) {
      showAlert("Отправьте геолокацию кнопкой в чате бота — координаты не показываем другим.");
    }
  };

  if (compact) {
    return (
      <button
        type="button"
        className={`geo-pill ${hasLocation ? "on" : ""}`}
        onClick={() => void update()}
      >
        {hasLocation ? "📍 Рядом" : "📍 Гео"}
      </button>
    );
  }

  return (
    <div className={`location-bar ${hasLocation ? "active" : ""}`}>
      <span className="location-dot">{hasLocation ? "●" : "○"}</span>
      <span className="location-text">
        {hasLocation ? "Поиск рядом с вами" : "Включите гео — покажем ближайшее"}
      </span>
      <button type="button" className="location-btn" onClick={() => void update()}>
        {hasLocation ? "Обновить" : "Включить"}
      </button>
    </div>
  );
}
