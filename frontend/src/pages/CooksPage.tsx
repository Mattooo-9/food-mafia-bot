import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { AssistantSearch, Cook } from "../types";

export default function CooksPage() {
  const [draft, setDraft] = useState("");
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

  const runSearch = (q: string) => {
    setDraft(q);
    setQuery(q);
  };

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

  const empty = Boolean(query.trim()) && !loading && result && result.total_cooks === 0;
  const hasCooks = !loading && (result?.total_cooks ?? 0) > 0;

  return (
    <div className="page">
      <h1 className="page-title">Повара</h1>

      <AiSearchHero
        draft={draft}
        onDraftChange={setDraft}
        onSearch={runSearch}
        onClear={() => runSearch("")}
        suggestions={result?.suggestions}
        showChips={(result?.suggestions?.length ?? 0) > 0}
        placeholder={result?.context?.search_placeholder ?? "Категория или имя"}
      />

      <header className="section-bar">
        <h2>{query.trim() || "Рядом"}</h2>
        {hasCooks && <span className="section-meta">{result!.total_cooks}</span>}
      </header>

      {loading ? (
        <Spinner />
      ) : empty ? (
        <p className="empty-line">Не найдено</p>
      ) : hasCooks ? (
        <AiResultGroups groups={result!.groups} onToggleFavoriteCook={toggleFavorite} />
      ) : null}
    </div>
  );
}
