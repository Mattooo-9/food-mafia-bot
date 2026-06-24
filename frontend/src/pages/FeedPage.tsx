import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import LocationBar from "../components/LocationBar";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { AssistantSearch, Food } from "../types";

export default function FeedPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AssistantSearch | null>(null);
  const [loading, setLoading] = useState(true);
  const [searched, setSearched] = useState(false);

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

  const runSearch = (q: string) => {
    setDraft(q);
    setQuery(q);
    setSearched(Boolean(q));
  };

  useEffect(() => {
    const fromProfile = (location.state as { q?: string } | null)?.q;
    if (fromProfile) {
      runSearch(fromProfile);
      navigate(".", { replace: true, state: null });
    }
  }, [location.state, navigate]);

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

  const empty = searched && !loading && result && result.total_foods === 0;

  return (
    <div className="page">
      <h1 className="page-title">Еда Рядом</h1>

      <AiSearchHero draft={draft} onDraftChange={setDraft} onSearch={runSearch} />
      <LocationBar />

      {result && (
        <div className="ai-message">
          <span className="ai-message-icon">🤖</span>
          <p>{result.message}</p>
          {result.companion && !result.message.includes(result.companion) && (
            <p className="hint" style={{ marginTop: 6 }}>{result.companion}</p>
          )}
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : empty ? (
        <div className="empty">
          <span className="emoji">🔮</span>
          Ничего не нашёл — попробуйте «борщ», «суп» или «салат»
        </div>
      ) : (
        <AiResultGroups groups={result?.groups ?? []} onToggleFavoriteFood={toggleFavorite} />
      )}
    </div>
  );
}
