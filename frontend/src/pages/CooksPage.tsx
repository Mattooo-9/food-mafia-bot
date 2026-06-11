import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import CookCard from "../components/CookCard";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { Cook } from "../types";

const DISTANCES: { value: number | null; label: string }[] = [
  { value: null, label: "Любое" },
  { value: 500, label: "500 м" },
  { value: 1000, label: "1 км" },
  { value: 3000, label: "3 км" },
  { value: 5000, label: "5 км" },
  { value: 10000, label: "10 км" },
];

export default function CooksPage() {
  const [cooks, setCooks] = useState<Cook[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxDistance, setMaxDistance] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCooks(await api.getCooks(maxDistance, null));
    } finally {
      setLoading(false);
    }
  }, [maxDistance]);

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
      <h1 className="page-title">Повара рядом 👨‍🍳</h1>
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
      {loading ? (
        <Spinner />
      ) : cooks.length === 0 ? (
        <div className="empty">
          <span className="emoji">👨‍🍳</span>Поваров поблизости пока нет
        </div>
      ) : (
        cooks.map((cook) => <CookCard key={cook.id} cook={cook} onToggleFavorite={toggleFavorite} />)
      )}
    </div>
  );
}
