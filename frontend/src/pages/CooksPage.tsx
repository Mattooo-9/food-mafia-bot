import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import LocationBar from "../components/LocationBar";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { AssistantSearch, Cook } from "../types";

export default function CooksPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AssistantSearch | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      setResult(await api.aiSearch(q, "cooks"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(query);
  }, [query, load]);

  const toggleFavorite = async (cook: Cook) => {
    haptic();
    if (cook.is_favorite) await api.removeFavoriteCook(cook.id);
    else await api.addFavoriteCook(cook.id);
    setResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        groups: prev.groups.map((g) => ({
          ...g,
          cooks: g.cooks.map((c) =>
            c.id === cook.id ? { ...c, is_favorite: !c.is_favorite } : c,
          ),
        })),
      };
    });
  };

  const empty = !loading && result && result.total_cooks === 0;

  return (
    <div className="page">
      <h1 className="page-title">Повара</h1>

      <AiSearchHero value={query} onChange={setQuery} placeholder="Например: повар с выпечкой рядом…" />
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
          <span className="emoji">👨‍🍳</span>
          Поваров не нашёл — укажите геолокацию или измените запрос
        </div>
      ) : (
        <AiResultGroups groups={result?.groups ?? []} onToggleFavoriteCook={toggleFavorite} />
      )}
    </div>
  );
}
