import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import FoodCard from "../components/FoodCard";
import LocationBar from "../components/LocationBar";
import SearchBar from "../components/SearchBar";
import Spinner from "../components/Spinner";
import { DISTANCES, FEEDS, RATINGS, sortRu } from "../constants";
import { haptic } from "../telegram";
import type { Food, FoodFilters, FeedType } from "../types";
import { useUser } from "../UserContext";

export default function FeedPage() {
  const { user } = useUser();
  const hasLocation = user?.lat != null;

  const [filters, setFilters] = useState<FoodFilters>({
    category: null,
    feed: hasLocation ? "nearby" : "new",
    max_distance_m: null,
    min_rating: null,
    price_max: null,
    price_min: null,
    q: "",
  });
  const [categories, setCategories] = useState<string[]>([]);
  const [foods, setFoods] = useState<Food[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [priceMax, setPriceMax] = useState("");

  const effectiveFeed: FeedType =
    filters.q ? "new" : filters.feed === "nearby" && !hasLocation ? "new" : filters.feed;

  const sortedCategories = useMemo(() => sortRu(categories), [categories]);

  useEffect(() => {
    void api.getCategories().then((r) => setCategories(r.categories));
  }, []);

  useEffect(() => {
    if (!hasLocation && filters.feed === "nearby" && !filters.q) {
      setFilters((prev) => ({ ...prev, feed: "new" }));
    }
  }, [hasLocation, filters.feed, filters.q]);

  const setQuery = useCallback((q: string) => {
    setFilters((prev) => ({ ...prev, q }));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getFoods({ ...filters, feed: effectiveFeed });
      setFoods(result);
    } finally {
      setLoading(false);
    }
  }, [filters, effectiveFeed]);

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

  return (
    <div className="page">
      <h1 className="page-title">Еда Рядом</h1>

      <SearchBar value={filters.q} onChange={setQuery} placeholder="Блюдо, повар, описание…" />
      <LocationBar />

      {!filters.q && (
        <div className="chips">
          {FEEDS.map((f) => (
            <button
              key={f.id}
              className={`chip ${effectiveFeed === f.id ? "active" : ""}`}
              onClick={() => setFilters((prev) => ({ ...prev, feed: f.id }))}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      <div className="chips">
        <button className="chip" onClick={() => setShowFilters((v) => !v)}>
          Фильтры {showFilters ? "▲" : "▼"}
        </button>
        <button
          className={`chip ${filters.category === null ? "active" : ""}`}
          onClick={() => setFilters((prev) => ({ ...prev, category: null }))}
        >
          Все
        </button>
        {sortedCategories.map((c) => (
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
            <label>Цена до, ⭐</label>
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
          {filters.q ? "Ничего не найдено" : "Пока нет блюд по выбранным фильтрам"}
        </div>
      ) : (
        foods.map((food) => <FoodCard key={food.id} food={food} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
