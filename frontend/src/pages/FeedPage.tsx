import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import LocationBar from "../components/LocationBar";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { AssistantSearch, Food } from "../types";

export default function FeedPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AssistantSearch | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      setResult(await api.aiSearch(q, "feed"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(query);
  }, [query, load]);

  const toggleFavorite = async (food: Food) => {
    haptic();
    if (food.is_favorite) await api.removeFavoriteFood(food.id);
    else await api.addFavoriteFood(food.id);
    setResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        groups: prev.groups.map((g) => ({
          ...g,
          foods: g.foods.map((f) =>
            f.id === food.id ? { ...f, is_favorite: !f.is_favorite } : f,
          ),
        })),
      };
    });
  };

  const empty = !loading && result && result.total_foods === 0;

  return (
    <div className="page">
      <h1 className="page-title">Еда Рядом</h1>

      <AiSearchHero value={query} onChange={setQuery} />
      <LocationBar />

      {result && (
        <div className="ai-message">
          <span className="ai-message-icon">🤖</span>
          <p>{result.message}</p>
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : empty ? (
        <div className="empty">
          <span className="emoji">🔮</span>
          Пока пусто — попробуйте «пирог», «суп рядом» или «недорого»
        </div>
      ) : (
        <AiResultGroups groups={result?.groups ?? []} onToggleFavoriteFood={toggleFavorite} />
      )}
    </div>
  );
}
