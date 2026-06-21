import { useState } from "react";
import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";

export default function LocationBar() {
  const { user, requestLocation } = useUser();
  const [locating, setLocating] = useState(false);

  const hasLocation = user?.lat != null && user?.lon != null;

  const update = async () => {
    setLocating(true);
    const ok = await requestLocation();
    setLocating(false);
    haptic(ok ? "success" : "error");
    if (!ok) {
      showAlert("Не удалось определить. Отправьте геолокацию кнопкой в чате бота.");
    }
  };

  return (
    <div className={`location-bar ${hasLocation ? "active" : ""}`}>
      <span className="location-dot">{hasLocation ? "●" : "○"}</span>
      <span className="location-text">
        {hasLocation
          ? `Рядом с вами · ${user!.lat!.toFixed(3)}, ${user!.lon!.toFixed(3)}`
          : "Геолокация не указана — поиск по расстоянию ограничен"}
      </span>
      <button type="button" className="location-btn" disabled={locating} onClick={() => void update()}>
        {locating ? "…" : hasLocation ? "Обновить" : "Определить"}
      </button>
    </div>
  );
}
