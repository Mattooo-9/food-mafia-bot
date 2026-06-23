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
    if (user?.wellness_consent) {
      void api.getWellness().then((w) => setTip(w.message));
    }
  }, [user?.wellness_consent]);

  if (!user) return null;

  const toggle = async () => {
    setSaving(true);
    try {
      const next = !user.wellness_consent;
      const w = await api.setWellness(next, diet || null);
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

  return (
    <div className="card wellness-card">
      <div className="row between">
        <strong>🌿 Гармония питания</strong>
        <label className="toggle">
          <input
            type="checkbox"
            checked={user.wellness_consent}
            disabled={saving}
            onChange={() => void toggle()}
          />
          <span />
        </label>
      </div>
      <p className="hint" style={{ marginTop: 8 }}>
        Анонимные подсказки по балансу — только с вашего согласия. История поиска сохраняется
        только при включённой опции.
      </p>
      {user.wellness_consent && (
        <>
          {tip && <p className="wellness-tip">{tip}</p>}
          <div className="field" style={{ marginTop: 10 }}>
            <input
              placeholder="Предпочтения: без сладкого, легко…"
              value={diet}
              onChange={(e) => setDiet(e.target.value)}
              onBlur={() => {
                if (diet !== (user.diet_preference ?? "")) {
                  void api.setWellness(true, diet || null).then(() => refresh());
                }
              }}
            />
          </div>
        </>
      )}
    </div>
  );
}
