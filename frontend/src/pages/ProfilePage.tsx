import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import AccountHistory from "../components/AccountHistory";
import ReferralCard from "../components/ReferralCard";
import LocationBar from "../components/LocationBar";
import PaymentWallet from "../components/PaymentWallet";
import Spinner from "../components/Spinner";
import Stars from "../components/Stars";
import { haptic, showAlert } from "../telegram";
import type { Cook, Order } from "../types";
import { useUser } from "../UserContext";

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, refresh } = useUser();
  const [subscriptions, setSubscriptions] = useState<Cook[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [searches, setSearches] = useState<Awaited<ReturnType<typeof api.getSearchHistory>>>([]);
  const [editing, setEditing] = useState(false);
  const [cookName, setCookName] = useState("");
  const [cookDescription, setCookDescription] = useState("");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void Promise.all([api.getSubscriptions(), api.getMyOrders(), api.getSearchHistory()]).then(
      ([subs, ords, hist]) => {
        setSubscriptions(subs);
        setOrders(ords);
        setSearches(hist);
      },
    );
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

  const unsubscribe = async (cook: Cook) => {
    haptic();
    await api.unsubscribe(cook.id);
    setSubscriptions((prev) => prev.filter((c) => c.id !== cook.id));
  };

  return (
    <div className="page">
      <h1 className="page-title">Профиль</h1>

      <LocationBar />

      <AccountHistory
        searches={searches}
        orders={orders}
        onClearSearches={() => {
          void api.clearSearchHistory().then(() => setSearches([]));
        }}
        onPickSearch={(q) => navigate("/", { state: { q } })}
      />

      <ReferralCard />

      <div className="card">
        <strong>{user.first_name ?? user.username ?? `id${user.tg_id}`}</strong>
      </div>

      {user.is_cook && (
        <PaymentWallet savedAddress={user.ton_wallet_address} onSaved={() => void refresh()} />
      )}

      {user.is_cook ? (
        <div className="card">
          <div className="row between">
            <strong>{user.cook_name ?? "Моя кухня"}</strong>
            <span className={`badge ${user.is_online ? "online" : "offline"}`}>
              {user.is_online ? "онлайн" : "оффлайн"}
            </span>
          </div>
          <div style={{ marginTop: 6 }}>
            <Stars rating={user.rating_avg} count={user.rating_count} />
          </div>
          {user.cook_description && <p>{user.cook_description}</p>}
          <div className="btn-row">
            <button className="btn small" onClick={() => void toggleOnline()}>
              {user.is_online ? "Оффлайн" : "Онлайн"}
            </button>
            <button className="btn small secondary" onClick={() => setEditing((v) => !v)}>
              {editing ? "Скрыть" : "Редактировать"}
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <strong>Стать поваром</strong>
          <p className="hint">Добавьте блюда — покупатели увидят вас в ленте.</p>
          <button className="btn" onClick={() => setEditing(true)}>
            Создать профиль
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
              placeholder="Кухня Марии"
              maxLength={128}
            />
          </div>
          <div className="field">
            <label>О себе</label>
            <textarea
              value={cookDescription}
              onChange={(e) => setCookDescription(e.target.value)}
              placeholder="О вашей кухне"
              maxLength={2000}
            />
          </div>
          <div className="field">
            <label>Фото</label>
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

      {subscriptions.length > 0 && (
        <>
          <h2 className="section-title">Подписки ({subscriptions.length})</h2>
          {subscriptions.map((cook) => (
            <div className="card row between" key={cook.id}>
              <strong>{cook.cook_name ?? cook.first_name ?? "Повар"}</strong>
              <button className="btn small secondary" onClick={() => void unsubscribe(cook)}>
                Отписаться
              </button>
            </div>
          ))}
        </>
      )}

      <p className="footer-hint">Справка: /help в чате бота</p>
    </div>
  );
}
