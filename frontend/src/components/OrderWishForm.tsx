import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, ApiError } from "../api";
import { haptic, hideKeyboard, showAlert } from "../telegram";

interface Props {
  onCreated: () => void;
}

export default function OrderWishForm({ onCreated }: Props) {
  const location = useLocation();
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");
  const [budget, setBudget] = useState("");
  const [portions, setPortions] = useState(1);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const prefill = (location.state as { wishTitle?: string } | null)?.wishTitle;
    if (prefill) setTitle(prefill);
  }, [location.state]);

  const submit = async () => {
    const t = title.trim();
    if (t.length < 2) {
      showAlert("Опишите, что хотите — например «домашний борщ»");
      return;
    }
    setSaving(true);
    hideKeyboard();
    try {
      await api.createWish({
        title: t,
        details: details.trim(),
        budget_max: budget ? Number(budget) : null,
        portions,
      });
      haptic("success");
      setTitle("");
      setDetails("");
      setBudget("");
      setPortions(1);
      onCreated();
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось опубликовать");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card wish-form">
      <strong>📋 Запрос поварам</strong>
      <p className="hint">Опишите блюдо — повара рядом сами возьмут заказ</p>
      <div className="field">
        <input
          placeholder="Например: суп на двоих"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>
      <div className="field">
        <textarea
          placeholder="Детали: без острого, к 19:00…"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          rows={2}
        />
      </div>
      <div className="row" style={{ gap: 8 }}>
        <div className="field" style={{ flex: 1 }}>
          <input
            type="number"
            placeholder="Бюджет ⭐"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
        </div>
        <div className="qty-control">
          <button type="button" onClick={() => setPortions((p) => Math.max(1, p - 1))}>
            −
          </button>
          <span>{portions}</span>
          <button type="button" onClick={() => setPortions((p) => p + 1)}>
            +
          </button>
        </div>
      </div>
      <button className="btn" disabled={saving} onClick={() => void submit()}>
        Опубликовать запрос
      </button>
    </div>
  );
}
