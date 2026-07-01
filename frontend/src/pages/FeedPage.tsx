import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import HomeHeader from "../components/HomeHeader";
import Spinner from "../components/Spinner";
import { feedHasList, feedSectionTitle } from "../feedState";
import { t } from "../i18n";
import { haptic, showAlert } from "../telegram";
import type { AssistantSearch, Food } from "../types";

export default function FeedPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AssistantSearch | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      setResult(await api.aiSearch(q, "feed"));
    } catch (e) {
      showAlert(e instanceof ApiError ? e.message : "Не удалось загрузить");
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

  useEffect(() => {
    const fromProfile = (location.state as { q?: string } | null)?.q;
    if (fromProfile) {
      runSearch(fromProfile);
      navigate(".", { replace: true, state: null });
    }
  }, [location.state, navigate]);

  useEffect(() => {
    if (
      result?.action === "orders" &&
      result.state === "search_empty" &&
      query.trim()
    ) {
      navigate("/orders", { state: { wishTitle: query.trim() }, replace: false });
    }
  }, [result?.action, result?.state, query, navigate]);

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

  const state = result?.state ?? "browse";
  const searched = Boolean(query.trim());
  const showList = result && feedHasList(state, result.total_foods);
  const companion = result?.companion?.trim() ?? "";
  const emptyLine =
    !loading && !showList && !companion
      ? state === "no_geo"
        ? t("feed.no_geo")
        : state === "no_supply"
          ? t("feed.no_supply")
          : ""
      : "";

  return (
    <div className="home-shell">
      <HomeHeader hasLocation={result?.has_location ?? false} />

      <section className="home-section">
        <div className="panel panel-search">
          <AiSearchHero
            draft={draft}
            onDraftChange={setDraft}
            onSearch={runSearch}
            onClear={() => runSearch("")}
            suggestions={result?.suggestions}
            showChips={!searched && (result?.suggestions?.length ?? 0) > 0}
            placeholder={result?.context?.search_placeholder ?? t("feed.search_placeholder")}
          />
          {companion && <p className="feed-companion">{companion}</p>}
        </div>
      </section>

      <section className="home-section home-feed">
        <header className="section-bar">
          <h2>{feedSectionTitle(state, query, result?.context)}</h2>
          {showList && <span className="section-meta">{result!.total_foods}</span>}
        </header>

        {loading ? (
          <Spinner />
        ) : showList ? (
          <AiResultGroups groups={result!.groups} onToggleFavoriteFood={toggleFavorite} />
        ) : emptyLine ? (
          <p className="empty-line panel panel-compact">{emptyLine}</p>
        ) : null}
      </section>
    </div>
  );
}
