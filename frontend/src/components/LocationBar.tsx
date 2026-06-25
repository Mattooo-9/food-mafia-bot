import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";
import AppIcon from "./icons";

interface Props {
  compact?: boolean;
  active?: boolean;
}

export default function LocationBar({ compact = false, active }: Props) {
  const { user, requestLocation } = useUser();
  const hasLocation = active ?? (user?.lat != null && user?.lon != null);

  const update = async () => {
    const ok = await requestLocation();
    haptic(ok ? "success" : "error");
    if (!ok) {
      showAlert("Отправьте геолокацию кнопкой в чате бота.");
    }
  };

  if (compact) {
    return (
      <button
        type="button"
        className={`geo-pill ${hasLocation ? "on" : ""}`}
        onClick={() => void update()}
        aria-label={hasLocation ? "Геолокация включена" : "Включить геолокацию"}
      >
        <AppIcon name={hasLocation ? "geoOn" : "geo"} size={16} />
        <span>{hasLocation ? "Рядом" : "Гео"}</span>
      </button>
    );
  }

  return (
    <div className={`location-bar panel ${hasLocation ? "active" : ""}`}>
      <AppIcon name={hasLocation ? "geoOn" : "geo"} size={18} />
      <span className="location-text">{hasLocation ? "Поиск по расстоянию" : "Геолокация выключена"}</span>
      <button type="button" className="location-btn" onClick={() => void update()}>
        {hasLocation ? "Обновить" : "Включить"}
      </button>
    </div>
  );
}
