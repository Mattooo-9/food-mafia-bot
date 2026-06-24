import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";

export default function WellnessCard() {
  const { user, refresh } = useUser();
  const [tip, setTip] = useState("");
  const [diet, setDiet] = useState(user?.diet_preference ?? "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void api.getWellness().then((w) => setTip(w.message));
  }, [user?.id, user?.wellness_consent, user?.diet_preference]);

  useEffect(() => {
    setDiet(user?.diet_preference ?? "");
  }, [user?.diet_preference]);

  if (!user) return null;

  const togglePersonalize = async () => {
    setSaving(true);
    try {
      const w = await api.setWellness(!user.wellness_consent, diet || null);
      setTip(w.message);
      haptic("success");
      await refresh();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  };

  const saveDiet = async () => {
    if (diet === (user.diet_preference ?? "")) return;
    try {
      const w = await api.setWellness(user.wellness_consent, diet || null);
      setTip(w.message);
      await refresh();
    } catch {
      /* ignore blur errors */
    }
  };

  return (
    <div className="card wellness-card">
      <strong>🌿 Подсказки по балансу</strong>
      {tip && <p className="wellness-tip">{tip}</p>}
      <div className="field" style={{ marginTop: 10 }}>
        <input
          placeholder="Предпочтения: без мяса, легко…"
          value={diet}
          onChange={(e) => setDiet(e.target.value)}
          onBlur={() => void saveDiet()}
        />
      </div>
      <div className="row between" style={{ marginTop: 12 }}>
        <span className="hint">Учитывать прошлые запросы</span>
        <label className="toggle">
          <input
            type="checkbox"
            checked={user.wellness_consent}
            disabled={saving}
            onChange={() => void togglePersonalize()}
          />
          <span />
        </label>
      </div>
    </div>
  );
}
