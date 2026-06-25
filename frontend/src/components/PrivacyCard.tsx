import { api, ApiError } from "../api";
import { haptic, showAlert } from "../telegram";

interface Props {
  onCleared: () => void;
}

export default function PrivacyCard({ onCleared }: Props) {
  const wipe = async () => {
    haptic();
    try {
      await api.wipePrivacy();
      haptic("success");
      onCleared();
      showAlert("История поиска и память ИИ удалены. Геолокация и заказы сохранены.");
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось очистить");
    }
  };

  return (
    <div className="card privacy-card gloss-card">
      <strong>Приватность</strong>
      <p className="hint privacy-text">
        Имена других пользователей скрыты. Координаты не видны никому. Данные привязаны только к вашему Telegram.
      </p>
      <button type="button" className="btn small secondary" onClick={() => void wipe()}>
        Стереть память ИИ и историю
      </button>
    </div>
  );
}
