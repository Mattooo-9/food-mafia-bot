import type { FeedContext } from "./types";

export type FeedState =
  | "browse"
  | "search_results"
  | "search_empty"
  | "no_supply"
  | "no_geo";

export interface FeedActivity {
  active_orders: number;
  open_wishes: number;
  claimed_wishes: number;
}

export function feedSectionTitle(
  state: FeedState,
  query: string,
  context?: FeedContext | null,
): string {
  if (state === "search_results") return query.trim() || "Результат";
  if (state === "search_empty") return "Поиск";
  return context?.section_label ?? "Рядом";
}

export function feedHasList(state: FeedState, totalFoods: number): boolean {
  return totalFoods > 0 && state !== "search_empty";
}

export function feedShowWish(state: FeedState, action: string | null): boolean {
  return state === "search_empty" && action === "create_wish";
}

export function activitySummary(activity: FeedActivity | null | undefined): string | null {
  if (!activity) return null;
  const parts: string[] = [];
  if (activity.active_orders > 0) {
    parts.push(`${activity.active_orders} заказ`);
  }
  if (activity.open_wishes > 0) {
    parts.push(`${activity.open_wishes} запрос`);
  }
  if (activity.claimed_wishes > 0 && activity.open_wishes === 0) {
    parts.push(`${activity.claimed_wishes} в работе`);
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}
