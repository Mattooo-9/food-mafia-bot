import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import AiMessage from "../components/AiMessage";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import HomeAiPicks from "../components/HomeAiPicks";
import HomeQuickNav from "../components/HomeQuickNav";
import LocationBar from "../components/LocationBar";
import Spinner from "../components/Spinner";
import { useUser } from "../UserContext";
import { haptic, showAlert } from "../telegram";
import type { AssistantSearch, Food } from "../types";

export default function FeedPage() {
  const { user } = useUser();
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
    } catch (e) {
      showAlert(e instanceof ApiError ? e.message : "Не удалось загрузить ленту");
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
      <div className="home-orb home-orb-c" aria-hidden />

      <header className="home-header gloss-card">
        <div>
          <p className="home-greet">Привет, {name}</p>
          <h1 className="home-title">Еда Рядом</h1>
        </div>
        <div className="home-header-badge">AI</div>
      </header>

      <AiSearchHero
        draft={draft}
        onDraftChange={setDraft}
        onSearch={runSearch}
        onClear={() => runSearch("")}
        suggestions={result?.suggestions}
      />

      <LocationBar />

      {result && !loading && (
        <div className="home-stats gloss-card">
          <span>{result.total_foods} блюд</span>
          <span>{result.intent.category || "все категории"}</span>
          {result.intent.max_distance_m != null && (
            <span>до {Math.round(result.intent.max_distance_m / 1000)} км</span>
          )}
        </div>
      )}

      {result && <AiMessage result={result} wishQuery={query} />}

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
          Ничего рядом — нажмите «Запрос поварам» выше
        </div>
      ) : (
        <AiResultGroups groups={result?.groups ?? []} onToggleFavoriteFood={toggleFavorite} />
      )}
    </div>
  );
}
