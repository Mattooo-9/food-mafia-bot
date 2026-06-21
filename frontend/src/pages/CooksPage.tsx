import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import CookCard from "../components/CookCard";
import DistanceSlider from "../components/DistanceSlider";
import LocationBar from "../components/LocationBar";
import SearchBar from "../components/SearchBar";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { Cook } from "../types";
import { useUser } from "../UserContext";

const DEFAULT_DISTANCE = 3000;

export default function CooksPage() {
  const { user } = useUser();
  const hasLocation = user?.lat != null;

  const [cooks, setCooks] = useState<Cook[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxDistance, setMaxDistance] = useState(DEFAULT_DISTANCE);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCooks(await api.getCooks(hasLocation ? maxDistance : null, null, query));
    } finally {
      setLoading(false);
    }
  }, [hasLocation, maxDistance, query]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleFavorite = async (cook: Cook) => {
    haptic();
    if (cook.is_favorite) {
      await api.removeFavoriteCook(cook.id);
    } else {
      await api.addFavoriteCook(cook.id);
    }
    setCooks((prev) =>
      prev.map((c) => (c.id === cook.id ? { ...c, is_favorite: !c.is_favorite } : c)),
    );
  };

  return (
    <div className="page">
      <h1 className="page-title">Повара</h1>

      <SearchBar value={query} onChange={setQuery} placeholder="Имя кухни, повар…" />
      <LocationBar />

      <DistanceSlider value={maxDistance} onChange={setMaxDistance} />

      {loading ? (
        <Spinner />
      ) : cooks.length === 0 ? (
        <div className="empty">
          <span className="emoji">👨‍🍳</span>
          {query ? "Поваров не найдено" : hasLocation ? "Поваров поблизости пока нет" : "Укажите геолокацию для поиска рядом"}
        </div>
      ) : (
        cooks.map((cook) => <CookCard key={cook.id} cook={cook} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
