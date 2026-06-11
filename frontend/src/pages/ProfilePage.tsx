import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import Spinner from "../components/Spinner";
import Stars from "../components/Stars";
import { haptic, showAlert } from "../telegram";
import type { Cook } from "../types";
import { useUser } from "../UserContext";

export default function ProfilePage() {
  const { user, refresh, requestLocation } = useUser();
  const [subscriptions, setSubscriptions] = useState<Cook[]>([]);
  const [editing, setEditing] = useState(false);
  const [cookName, setCookName] = useState("");
  const [cookDescription, setCookDescription] = useState("");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);

  useEffect(() => {
    void api.getSubscriptions().then(setSubscriptions);
  }, []);

  useEffect(() => {
    if (user) {
      setCookName(user.cook_name ?? "");
      setCookDescription(user.cook_description ?? "");
    }
  }, [user]);

  if (!user) return <Spinner />;

  const saveProfile = async () => {
    if (cookName.trim().length < 2) {
      showAlert("Укажите название кухни (минимум 2 символа)");
      return;
    }
    setSaving(true);
    try {
      let photoUrl: string | undefined;
      if (photoFile) {
        photoUrl = await api.uploadPhoto(photoFile);
      }
      await api.updateCookProfile({
        cook_name: cookName.trim(),
        cook_description: cookDescription.trim(),
        ...(photoUrl ? { cook_photo: photoUrl } : {}),
      });
      haptic("success");
      setEditing(false);
      await refresh();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось сохранить профиль");
    } finally {
      setSaving(false);
    }
  };

  const toggleOnline = async () => {
    haptic();
    await api.updateCookProfile({ is_online: !user.is_online });
    await refresh();
  };

  const updateLocation = async () => {
    setLocating(true);
    const ok = await requestLocation();
    setLocating(false);
    if (ok) {
      haptic("success");
      showAlert("Геолокация обновлена!");
    } else {
      showAlert("Не удалось получить геолокацию. Отправьте её через бота кнопкой «📍».");
    }
  };

  const unsubscribe = async (cook: Cook) => {
    haptic();
    await api.unsubscribe(cook.id);
    setSubscriptions((prev) => prev.filter((c) => c.id !== cook.id));
  };

  return (
    <div className="page">
      <h1 className="page-title">Профиль 👤</h1>

      <div className="card">
        <strong>{user.first_name ?? user.username ?? `id${user.tg_id}`}</strong>
        <div className="food-meta" style={{ marginTop: 6 }}>
          <span>
            📍{" "}
            {user.lat != null
              ? `${user.lat.toFixed(4)}, ${user.lon?.toFixed(4)}`
              : "геолокация не указана"}
          </span>
        </div>
        <div className="btn-row">
          <button className="btn small secondary" disabled={locating} onClick={() => void updateLocation()}>
            {locating ? "Определяем..." : "📍 Обновить геолокацию"}
          </button>
        </div>
      </div>

      {user.is_cook ? (
        <div className="card">
          <div className="row between">
            <strong>👨‍🍳 {user.cook_name ?? "Мой профиль повара"}</strong>
            <span className={`badge ${user.is_online ? "online" : "offline"}`}>
              {user.is_online ? "● онлайн" : "○ оффлайн"}
            </span>
          </div>
          <div style={{ marginTop: 6 }}>
            <Stars rating={user.rating_avg} count={user.rating_count} />
          </div>
          {user.cook_description && <p>{user.cook_description}</p>}
          <div className="btn-row">
            <button className="btn small" onClick={() => void toggleOnline()}>
              {user.is_online ? "Уйти в оффлайн" : "Выйти в онлайн"}
            </button>
            <button className="btn small secondary" onClick={() => setEditing((v) => !v)}>
              {editing ? "Скрыть" : "Редактировать"}
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <strong>Хотите готовить и продавать?</strong>
          <p className="hint">
            Создайте профиль повара, добавьте блюда — и покупатели рядом увидят вас в ленте.
          </p>
          <button className="btn" onClick={() => setEditing(true)}>
            👨‍🍳 Стать поваром
          </button>
        </div>
      )}

      {editing && (
        <div className="card">
          <div className="field">
            <label>Название кухни</label>
            <input
              value={cookName}
              onChange={(e) => setCookName(e.target.value)}
              placeholder="Например: Кухня Марии"
              maxLength={128}
            />
          </div>
          <div className="field">
            <label>О себе</label>
            <textarea
              value={cookDescription}
              onChange={(e) => setCookDescription(e.target.value)}
              placeholder="Расскажите о своей кухне"
              maxLength={2000}
            />
          </div>
          <div className="field">
            <label>Фото профиля</label>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <button className="btn" disabled={saving} onClick={() => void saveProfile()}>
            {saving ? "Сохраняем..." : "Сохранить"}
          </button>
        </div>
      )}

      <h2 className="section-title">Подписки 🔔 ({subscriptions.length})</h2>
      {subscriptions.length === 0 ? (
        <div className="empty">Вы пока ни на кого не подписаны</div>
      ) : (
        subscriptions.map((cook) => (
          <div className="card row between" key={cook.id}>
            <strong>{cook.cook_name ?? cook.first_name ?? "Повар"}</strong>
            <button className="btn small secondary" onClick={() => void unsubscribe(cook)}>
              Отписаться
            </button>
          </div>
        ))
      )}
    </div>
  );
}
