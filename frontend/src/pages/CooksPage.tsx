import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import CookCard from "../components/CookCard";
import LocationBar from "../components/LocationBar";
import SearchBar from "../components/SearchBar";
import Spinner from "../components/Spinner";
import { DISTANCES, RATINGS } from "../constants";
import { haptic } from "../telegram";
import type { Cook } from "../types";

export default function CooksPage() {
  const [cooks, setCooks] = useState<Cook[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxDistance, setMaxDistance] = useState<number | null>(null);
  const [minRating, setMinRating] = useState<number | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCooks(await api.getCooks(maxDistance, minRating, query));
    } finally {
      setLoading(false);
    }
  }, [maxDistance, minRating, query]);

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

      <div className="chips">
        {DISTANCES.map((d) => (
          <button
            key={d.label}
            className={`chip ${maxDistance === d.value ? "active" : ""}`}
            onClick={() => setMaxDistance(d.value)}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="chips">
        {RATINGS.map((r) => (
          <button
            key={r.label}
            className={`chip ${minRating === r.value ? "active" : ""}`}
            onClick={() => setMinRating(r.value)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : cooks.length === 0 ? (
        <div className="empty">
          <span className="emoji">👨‍🍳</span>
          {query ? "Поваров не найдено" : "Поваров поблизости пока нет"}
        </div>
      ) : (
        cooks.map((cook) => <CookCard key={cook.id} cook={cook} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
