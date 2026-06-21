import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import Spinner from "../components/Spinner";
import AiPriceHint from "../components/AiPriceHint";
import { haptic, showAlert } from "../telegram";
import type { CategorizeResult } from "../types";

export default function DishFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id == null;

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [categoryLabel, setCategoryLabel] = useState("");
  const [categoryPath, setCategoryPath] = useState("");
  const [portions, setPortions] = useState("1");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [existingPhoto, setExistingPhoto] = useState<string | null>(null);

  const applyPrice = useCallback((stars: number) => {
    setPrice(String(stars));
    haptic("success");
  }, []);

  useEffect(() => {
    if (!name.trim() && !description.trim()) return;
    const timer = window.setTimeout(() => {
      void api
        .categorize({ name, description })
        .then((r: CategorizeResult) => {
          setCategoryLabel(r.label);
          setCategoryPath(r.path);
        })
        .catch(() => {});
    }, 400);
    return () => window.clearTimeout(timer);
  }, [name, description]);

  useEffect(() => {
    if (isNew) return;
    void api
      .getFood(Number(id))
      .then((food) => {
        setName(food.name);
        setDescription(food.description);
        setPrice(String(food.price));
        setCategoryLabel(food.category);
        setCategoryPath(food.category);
        setPortions(String(food.portions));
        setExistingPhoto(food.photo);
      })
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const save = async () => {
    if (name.trim().length < 2) {
      setError("Укажите название (минимум 2 символа)");
      return;
    }
    const priceNum = Number(price);
    if (!priceNum || priceNum <= 0) {
      setError("Укажите цену или нажмите «Поставить» от ИИ");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      let photoUrl: string | null = existingPhoto;
      if (photoFile) {
        photoUrl = await api.uploadPhoto(photoFile);
      }
      const payload = {
        name: name.trim(),
        description: description.trim(),
        price: priceNum,
        portions: Math.max(0, Number(portions) || 0),
        cooking_time_minutes: 30,
        ...(photoUrl ? { photo: photoUrl } : {}),
      };
      if (isNew) {
        await api.createFood(payload);
      } else {
        await api.updateFood(Number(id), payload);
      }
      haptic("success");
      navigate("/my-kitchen");
    } catch (e) {
      haptic("error");
      const message = e instanceof ApiError ? e.message : "Не удалось сохранить блюдо";
      setError(message);
      showAlert(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="page">
      <h1 className="page-title">{isNew ? "Новое блюдо" : "Редактирование"}</h1>
      <p className="hint" style={{ margin: "0 4px 12px" }}>
        Напишите что готовите — категорию и цену подберёт ИИ
      </p>
      <div className="card">
        <div className="field">
          <label>Название</label>
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={128} placeholder="Борщ домашний" />
        </div>
        <div className="field">
          <label>Описание</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
            placeholder="Из чего готовите, порция на сколько человек"
          />
        </div>
        {categoryLabel && (
          <p className="search-hint">Категория: {categoryLabel}</p>
        )}
        <div className="field">
          <label>Порций в наличии</label>
          <input type="number" min={0} value={portions} onChange={(e) => setPortions(e.target.value)} />
        </div>
        <div className="field">
          <label>Цена, ⭐</label>
          <input type="number" min={1} value={price} onChange={(e) => setPrice(e.target.value)} placeholder="ИИ подскажет" />
          <AiPriceHint
            category={categoryPath}
            price={price}
            description={description}
            name={name}
            portions={portions}
            autoFill={isNew}
            onSuggest={applyPrice}
          />
        </div>
        <div className="field">
          <label>Фото</label>
          {existingPhoto && !photoFile && (
            <img src={existingPhoto} alt="" style={{ width: 90, height: 90, borderRadius: 10, objectFit: "cover", marginBottom: 8 }} />
          )}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button className="btn" disabled={saving} onClick={() => void save()}>
          {saving ? "Сохраняем..." : "Сохранить"}
        </button>
        {error && <div className="error-text">{error}</div>}
      </div>
    </div>
  );
}
