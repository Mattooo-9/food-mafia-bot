import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import FoodCard from "../components/FoodCard";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { Food, FoodFilters, FeedType } from "../types";
import { useUser } from "../UserContext";

const FEEDS: { id: FeedType; label: string }[] = [
  { id: "nearby", label: "📍 Рядом со мной" },
  { id: "new", label: "🆕 Новые" },
  { id: "popular", label: "🔥 Популярное" },
  { id: "cheap", label: "💸 Дешёвое" },
  { id: "fast", label: "⚡ Быстрые" },
];

const DISTANCES: { value: number | null; label: string }[] = [
  { value: null, label: "Любое расстояние" },
  { value: 500, label: "500 м" },
  { value: 1000, label: "1 км" },
  { value: 3000, label: "3 км" },
  { value: 5000, label: "5 км" },
  { value: 10000, label: "10 км" },
];

const RATINGS: { value: number | null; label: string }[] = [
  { value: null, label: "Любой рейтинг" },
  { value: 3, label: "3+" },
  { value: 4, label: "4+" },
  { value: 4.5, label: "4.5+" },
];

export default function FeedPage() {
  const { user, requestLocation } = useUser();
  const [filters, setFilters] = useState<FoodFilters>({
    feed: "nearby",
    category: null,
    max_distance_m: null,
    price_min: null,
    price_max: null,
    min_rating: null,
  });
  const [categories, setCategories] = useState<string[]>([]);
  const [foods, setFoods] = useState<Food[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [priceMax, setPriceMax] = useState("");

  useEffect(() => {
    void api.getCategories().then((r) => setCategories(r.categories));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getFoods(filters);
      setFoods(result);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleFavorite = async (food: Food) => {
    haptic();
    if (food.is_favorite) {
      await api.removeFavoriteFood(food.id);
    } else {
      await api.addFavoriteFood(food.id);
    }
    setFoods((prev) =>
      prev.map((f) => (f.id === food.id ? { ...f, is_favorite: !f.is_favorite } : f)),
    );
  };

  const hasLocation = user?.lat != null;

  return (
    <div className="page">
      <h1 className="page-title">Еда Рядом 🍲</h1>

      {!hasLocation && (
        <div className="banner">
          📍 Геолокация не указана — лента «рядом» недоступна.{" "}
          <button className="btn small" onClick={() => void requestLocation()}>
            Определить
          </button>
        </div>
      )}

      <div className="chips">
        {FEEDS.map((f) => (
          <button
            key={f.id}
            className={`chip ${filters.feed === f.id ? "active" : ""}`}
            onClick={() => setFilters((prev) => ({ ...prev, feed: f.id }))}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="chips">
        <button className="chip" onClick={() => setShowFilters((v) => !v)}>
          ⚙️ Фильтры {showFilters ? "▲" : "▼"}
        </button>
        <button
          className={`chip ${filters.category === null ? "active" : ""}`}
          onClick={() => setFilters((prev) => ({ ...prev, category: null }))}
        >
          Все
        </button>
        {categories.map((c) => (
          <button
            key={c}
            className={`chip ${filters.category === c ? "active" : ""}`}
            onClick={() => setFilters((prev) => ({ ...prev, category: c }))}
          >
            {c}
          </button>
        ))}
      </div>

      {showFilters && (
        <div className="card">
          <div className="field">
            <label>Расстояние</label>
            <select
              value={filters.max_distance_m ?? ""}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  max_distance_m: e.target.value ? Number(e.target.value) : null,
                }))
              }
            >
              {DISTANCES.map((d) => (
                <option key={d.label} value={d.value ?? ""}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Рейтинг повара</label>
            <select
              value={filters.min_rating ?? ""}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  min_rating: e.target.value ? Number(e.target.value) : null,
                }))
              }
            >
              {RATINGS.map((r) => (
                <option key={r.label} value={r.value ?? ""}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Цена до, ₽</label>
            <input
              type="number"
              min={0}
              placeholder="Без ограничения"
              value={priceMax}
              onChange={(e) => setPriceMax(e.target.value)}
              onBlur={() =>
                setFilters((prev) => ({
                  ...prev,
                  price_max: priceMax ? Number(priceMax) : null,
                }))
              }
            />
          </div>
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : foods.length === 0 ? (
        <div className="empty">
          <span className="emoji">🍽</span>
          Пока нет блюд по выбранным фильтрам
        </div>
      ) : (
        foods.map((food) => <FoodCard key={food.id} food={food} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
