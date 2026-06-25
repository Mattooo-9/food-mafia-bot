import { useEffect, useState, type CSSProperties } from "react";
import { api, ApiError } from "../api";
import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";
import type { WellnessInfo } from "../types";

const ACTIVITY_LEVELS = [
  { id: "sedentary", label: "Сидячий" },
  { id: "light", label: "Лёгкая" },
  { id: "moderate", label: "Умеренная" },
  { id: "active", label: "Активный" },
  { id: "intense", label: "Интенсивный" },
] as const;

const RAINBOW_COLORS: { key: string; css: string; label: string }[] = [
  { key: "red", css: "#e85d5d", label: "Красный" },
  { key: "orange", css: "#e89a4a", label: "Оранжевый" },
  { key: "yellow", css: "#d4b84a", label: "Жёлтый" },
  { key: "green", css: "#5cb87a", label: "Зелёный" },
  { key: "purple", css: "#9a6bc9", label: "Фиолетовый" },
  { key: "white", css: "#c8cdd4", label: "Белый" },
];

export default function WellnessCard() {
  const { user, refresh } = useUser();
  const [diet, setDiet] = useState(user?.diet_preference ?? "");
  const [activity, setActivity] = useState(user?.activity_level ?? "moderate");
  const [info, setInfo] = useState<WellnessInfo | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDiet(user?.diet_preference ?? "");
    setActivity(user?.activity_level ?? "moderate");
  }, [user?.diet_preference, user?.activity_level]);

  useEffect(() => {
    if (!user?.wellness_consent) {
      setInfo(null);
      return;
    }
    void api.getWellness().then(setInfo).catch(() => setInfo(null));
  }, [user?.wellness_consent, user?.id]);

  if (!user) return null;

  const save = async (opts: {
    consent?: boolean;
    dietPref?: string;
    activityLevel?: string;
  }) => {
    setSaving(true);
    try {
      const res = await api.setWellness(
        opts.consent ?? user.wellness_consent,
        opts.dietPref ?? (diet || null),
        opts.activityLevel ?? activity,
      );
      setInfo(res);
      haptic("success");
      await refresh();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  };

  const logWater = async () => {
    haptic();
    try {
      const res = await api.logWater();
      setInfo(res);
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось отметить воду");
    }
  };

  const kcalPct =
    info && info.calorie_target > 0
      ? Math.min(100, Math.round((info.calories_today / info.calorie_target) * 100))
      : 0;

  return (
    <div className="card panel wellness-card">
      <strong>Питание и здоровье</strong>

      <div className="field" style={{ marginTop: 10 }}>
        <label className="hint">Ограничения и предпочтения</label>
        <input
          placeholder="Без мяса, легко, без лактозы…"
          value={diet}
          onChange={(e) => setDiet(e.target.value)}
          onBlur={() => void save({})}
        />
      </div>

      <div className="field" style={{ marginTop: 10 }}>
        <label className="hint">Активность</label>
        <div className="btn-row wrap">
          {ACTIVITY_LEVELS.map((lvl) => (
            <button
              key={lvl.id}
              type="button"
              className={`btn small ${activity === lvl.id ? "" : "secondary"}`}
              disabled={saving}
              onClick={() => {
                setActivity(lvl.id);
                void save({ activityLevel: lvl.id });
              }}
            >
              {lvl.label}
            </button>
          ))}
        </div>
      </div>

      <div className="row between" style={{ marginTop: 12 }}>
        <span className="hint">Умные рекомендации</span>
        <label className="toggle">
          <input
            type="checkbox"
            checked={user.wellness_consent}
            disabled={saving}
            onChange={() => void save({ consent: !user.wellness_consent })}
          />
          <span />
        </label>
      </div>

      {user.wellness_consent && info && (
        <div className="wellness-body">
          <div className="wellness-kcal">
            <div className="row between">
              <span className="hint">Калории сегодня</span>
              <span>
                {info.calories_today} / {info.calorie_target} ккал
              </span>
            </div>
            <div className="wellness-bar">
              <div className="wellness-bar-fill" style={{ width: `${kcalPct}%` }} />
            </div>
            <p className="hint">
              Б/Ж/У: {info.protein_g} / {info.fat_g} / {info.carbs_g} г · приём ~{info.meal_budget} ккал
            </p>
          </div>

          <div className="wellness-rainbow">
            <span className="hint">Радуга продуктов ({info.rainbow_progress}%)</span>
            <div className="rainbow-dots">
              {RAINBOW_COLORS.map((c) => (
                <span
                  key={c.key}
                  className={`rainbow-dot ${(info.rainbow[c.key] ?? 0) > 0 ? "on" : ""}`}
                  style={{ "--dot": c.css } as CSSProperties}
                  title={c.label}
                />
              ))}
            </div>
          </div>

          <div className="wellness-water row between">
            <span>
              Вода {info.water_glasses}/{info.water_target}
            </span>
            <button type="button" className="btn small" onClick={() => void logWater()}>
              + стакан
            </button>
          </div>

          {info.water_reminder && <p className="wellness-tip">{info.water_reminder}</p>}
          {info.message && <p className="wellness-tip">{info.message}</p>}
          {info.harmony_hint && <p className="hint">{info.harmony_hint}</p>}
          {info.balance_hint && <p className="hint">{info.balance_hint}</p>}
          {info.meal_schedule && <p className="hint">{info.meal_schedule}</p>}
        </div>
      )}
    </div>
  );
}
