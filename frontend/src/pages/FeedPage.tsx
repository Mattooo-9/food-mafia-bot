import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import AiResultGroups from "../components/AiResultGroups";
import AiSearchHero from "../components/AiSearchHero";
import HomeHeader from "../components/HomeHeader";
import OnboardingStrip from "../components/OnboardingStrip";
import Spinner from "../components/Spinner";
import {
  activitySummary,
  feedHasList,
  feedSectionTitle,
  feedShowWish,
} from "../feedState";
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
  const activity = activitySummary(result?.activity);
  const showWish = result && feedShowWish(state, result.action);

  const openWish = () => {
    haptic();
    navigate("/orders", { state: { wishTitle: query.trim() } });
  };

  return (
    <div className="home-shell">
      <HomeHeader hasLocation={result?.has_location ?? false} />

      <OnboardingStrip />

      {(result?.context?.water_reminder || result?.context?.harmony_hint) && (
        <section className="home-section">
          <div className="panel panel-compact wellness-feed-hint">
            <p>{result.context.water_reminder}</p>
            {result.context.harmony_hint && <p>{result.context.harmony_hint}</p>}
            {result.context.calorie_summary && (
              <p className="hint">{result.context.calorie_summary}</p>
            )}
          </div>
        </section>
      )}

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
        </div>
      </section>

      {activity && !loading && (
        <section className="home-section">
          <button type="button" className="panel activity-row" onClick={() => navigate("/orders")}>
            <span className="activity-row-label">{t("feed.orders")}</span>
            <span className="activity-row-value">{activity}</span>
          </button>
        </section>
      )}

      {showWish && (
        <section className="home-section">
          <div className="panel panel-compact wish-panel">
            <button type="button" className="btn wish-panel-btn" onClick={openWish}>
              {t("feed.wish")}
            </button>
          </div>
        </section>
      )}

      <section className="home-section home-feed">
        <header className="section-bar">
          <h2>{feedSectionTitle(state, query, result?.context)}</h2>
          {showList && <span className="section-meta">{result!.total_foods}</span>}
        </header>

        {loading ? (
          <Spinner />
        ) : showList ? (
          <AiResultGroups groups={result!.groups} onToggleFavoriteFood={toggleFavorite} />
        ) : state === "no_geo" ? (
          <p className="empty-line panel panel-compact">{t("feed.no_geo")}</p>
        ) : state === "no_supply" ? (
          <p className="empty-line panel panel-compact">{t("feed.no_supply")}</p>
        ) : null}
      </section>
    </div>
  );
}
