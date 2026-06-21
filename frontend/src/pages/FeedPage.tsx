import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import CategoryColumn from "../components/CategoryColumn";
import DistanceSlider from "../components/DistanceSlider";
import FoodCard from "../components/FoodCard";
import LocationBar from "../components/LocationBar";
import SearchBar from "../components/SearchBar";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { CategoryGroup, CategorizeResult, Food, FoodFilters } from "../types";
import { useUser } from "../UserContext";

const DEFAULT_DISTANCE = 3000;

export default function FeedPage() {
  const { user } = useUser();
  const hasLocation = user?.lat != null;

  const [filters, setFilters] = useState<FoodFilters>({
    category: null,
    feed: "nearby",
    max_distance_m: DEFAULT_DISTANCE,
    min_rating: null,
    price_max: null,
    price_min: null,
    q: "",
  });
  const [categoryTree, setCategoryTree] = useState<CategoryGroup[]>([]);
  const [foods, setFoods] = useState<Food[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchHint, setSearchHint] = useState<CategorizeResult | null>(null);

  useEffect(() => {
    void api.getCategories().then((r) => setCategoryTree(r.groups));
  }, []);

  useEffect(() => {
    if (!filters.q) {
      setSearchHint(null);
      return;
    }
    const timer = window.setTimeout(() => {
      void api.categorize({ q: filters.q }).then(setSearchHint).catch(() => setSearchHint(null));
    }, 400);
    return () => window.clearTimeout(timer);
  }, [filters.q]);

  const setQuery = useCallback((q: string) => {
    setFilters((prev) => ({ ...prev, q }));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: FoodFilters = {
        ...filters,
        feed: "nearby",
        max_distance_m: hasLocation ? filters.max_distance_m : null,
      };
      const result = await api.getFoods(params);
      setFoods(result);
    } finally {
      setLoading(false);
    }
  }, [filters, hasLocation]);

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

      <SearchBar value={filters.q} onChange={setQuery} placeholder="Что хотите поесть?" />
      {searchHint && filters.q && (
        <p className="search-hint">Ищем: {searchHint.label}</p>
      )}

      <LocationBar />
      <DistanceSlider
        value={filters.max_distance_m ?? DEFAULT_DISTANCE}
        onChange={(max_distance_m) => setFilters((prev) => ({ ...prev, max_distance_m }))}
      />

      <CategoryColumn
        groups={categoryTree}
        selected={filters.category}
        onSelect={(category) => setFilters((prev) => ({ ...prev, category }))}
      />

      {loading ? (
        <Spinner />
      ) : foods.length === 0 ? (
        <div className="empty">
          <span className="emoji">🍽</span>
          {filters.q ? "Ничего не найдено рядом" : "Пока нет блюд по выбранным фильтрам"}
        </div>
      ) : (
        foods.map((food) => <FoodCard key={food.id} food={food} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
