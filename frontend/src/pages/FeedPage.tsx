import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import AiMessage from "../components/AiMessage";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import HomeAiPicks from "../components/HomeAiPicks";
import HomeHeader, { HomeInsight } from "../components/HomeHeader";
import HomeQuickNav from "../components/HomeQuickNav";
import Spinner from "../components/Spinner";
import { useUser } from "../UserContext";
import { haptic, showAlert } from "../telegram";
import type { AssistantSearch, Food, UserInsights } from "../types";

export default function FeedPage() {
  const { user } = useUser();
  const location = useLocation();
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AssistantSearch | null>(null);
  const [insights, setInsights] = useState<UserInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [searched, setSearched] = useState(false);

  const loadInsights = useCallback(async () => {
    try {
      setInsights(await api.getInsights());
    } catch {
      setInsights(null);
    }
  }, []);

  const load = useCallback(
    async (q: string) => {
      setLoading(true);
      try {
        const [search, dash] = await Promise.all([api.aiSearch(q, "feed"), api.getInsights()]);
        setResult(search);
        setInsights(dash);
      } catch (e) {
        showAlert(e instanceof ApiError ? e.message : "Не удалось загрузить ленту");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void load(query);
  }, [query, load]);

  useEffect(() => {
    void loadInsights();
  }, [loadInsights]);

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
    try {
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
    } catch (e) {
      haptic("error");
      showAlert(e instanceof ApiError ? e.message : "Не удалось обновить избранное");
    }
  };

  const empty = searched && !loading && result && result.total_foods === 0;
  const name = user?.first_name?.split(" ")[0] ?? "друг";
  const showHub = !searched && !loading;

  return (
    <div className="home-shell">
      <div className="home-orb home-orb-a" aria-hidden />
      <div className="home-orb home-orb-b" aria-hidden />

      <HomeHeader name={name} />

      <AiSearchHero
        draft={draft}
        onDraftChange={setDraft}
        onSearch={runSearch}
        onClear={() => runSearch("")}
        suggestions={result?.suggestions}
      />

      {insights && showHub && (
        <HomeInsight insights={insights} onOrders={() => navigate("/orders")} />
      )}

      {searched && result && <AiMessage result={result} wishQuery={query} />}

      {searched && result && !loading && (
        <div className="home-stats gloss-card">
          <span>{result.total_foods} блюд</span>
          <span>{result.intent.category || "всё рядом"}</span>
        </div>
      )}

      {showHub && (
        <>
          <HomeQuickNav />
          <HomeAiPicks />
        </>
      )}

      {loading ? (
        <Spinner />
      ) : empty ? (
        <div className="empty gloss-card">
          <span className="emoji">🔮</span>
          Пусто рядом — запрос поварам в сообщении выше
        </div>
      ) : searched ? (
        <AiResultGroups groups={result?.groups ?? []} onToggleFavoriteFood={toggleFavorite} />
      ) : null}
    </div>
  );
}
