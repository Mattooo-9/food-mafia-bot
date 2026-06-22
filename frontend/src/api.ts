import { getInitData } from "./telegram";
import type { Cook, Food, FoodFilters, MarketOverview, Order, OrderStatus, PaymentMethod, PriceSuggestion, ReferralInfo, Review, User, FoodEvaluation, Recommendation, CategoriesResponse, CategorizeResult, AssistantSearch, SearchHistoryItem } from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "X-Telegram-Init-Data": getInitData(),
    ...(options.headers as Record<string, string> | undefined),
  };
  if (options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let detail = `Ошибка ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // keep default message
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  getMe: () => request<User>("/api/me"),
  getSearchHistory: () => request<SearchHistoryItem[]>("/api/me/searches"),
  clearSearchHistory: () => request<{ ok: boolean }>("/api/me/searches", { method: "DELETE" }),
  getCurrency: () => request<{ currency: string; ton_per_star: number; referral_unit: string }>("/api/currency"),
  getAiMarket: () => request<MarketOverview>("/api/ai/market"),
  getPriceSuggestion: (
    category: string,
    opts?: {
      price?: number;
      description?: string;
      name?: string;
      portions?: number;
    },
  ) => {
    const params = new URLSearchParams({ category });
    if (opts?.price != null && opts.price > 0) params.set("price", String(opts.price));
    if (opts?.description) params.set("description", opts.description);
    if (opts?.name) params.set("name", opts.name);
    if (opts?.portions != null) params.set("portions", String(opts.portions));
    return request<PriceSuggestion>(`/api/ai/price-suggestion?${params}`);
  },
  getFoodEvaluation: (foodId: number) =>
    request<FoodEvaluation>(`/api/ai/food/${foodId}/evaluation`),
  getAiRecommendations: () => request<Recommendation[]>("/api/ai/recommendations"),
  getReferral: () => request<ReferralInfo>("/api/me/referral"),
  setWallet: (ton_wallet_address: string | null) =>
    request<User>("/api/me/wallet", {
      method: "POST",
      body: JSON.stringify({ ton_wallet_address }),
    }),
  setLocation: (lat: number, lon: number) =>
    request<User>("/api/me/location", { method: "POST", body: JSON.stringify({ lat, lon }) }),
  updateCookProfile: (data: {
    cook_name?: string;
    cook_description?: string;
    cook_photo?: string;
    is_online?: boolean;
  }) => request<User>("/api/me/cook-profile", { method: "POST", body: JSON.stringify(data) }),
  getCategories: () => request<CategoriesResponse>("/api/categories"),
  aiSearch: (q = "", scope: "feed" | "cooks" | "all" = "feed") => {
    const params = new URLSearchParams({ scope });
    if (q) params.set("q", q);
    return request<AssistantSearch>(`/api/ai/search?${params}`);
  },
  categorize: (opts: { name?: string; description?: string; q?: string }) => {
    const params = new URLSearchParams();
    if (opts.name) params.set("name", opts.name);
    if (opts.description) params.set("description", opts.description);
    if (opts.q) params.set("q", opts.q);
    return request<CategorizeResult>(`/api/ai/categorize?${params}`);
  },

  getFoods: (filters: FoodFilters) => {
    const params = new URLSearchParams({ feed: filters.feed });
    if (filters.q) params.set("q", filters.q);
    if (filters.category) params.set("category", filters.category);
    if (filters.max_distance_m != null) params.set("max_distance_m", String(filters.max_distance_m));
    if (filters.price_min != null) params.set("price_min", String(filters.price_min));
    if (filters.price_max != null) params.set("price_max", String(filters.price_max));
    if (filters.min_rating != null) params.set("min_rating", String(filters.min_rating));
    return request<Food[]>(`/api/foods?${params}`);
  },
  getFood: (id: number) => request<Food>(`/api/foods/${id}`),

  getCooks: (maxDistanceM: number | null, minRating: number | null, q = "") => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (maxDistanceM != null) params.set("max_distance_m", String(maxDistanceM));
    if (minRating != null) params.set("min_rating", String(minRating));
    return request<Cook[]>(`/api/cooks?${params}`);
  },
  getCook: (id: number) => request<Cook>(`/api/cooks/${id}`),
  getCookFoods: (id: number) => request<Food[]>(`/api/cooks/${id}/foods`),
  getCookReviews: (id: number) => request<Review[]>(`/api/cooks/${id}/reviews`),

  getMyFoods: () => request<Food[]>("/api/cook/foods"),
  createFood: (data: object) =>
    request<Food>("/api/cook/foods", { method: "POST", body: JSON.stringify(data) }),
  updateFood: (id: number, data: object) =>
    request<Food>(`/api/cook/foods/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteFood: (id: number) => request<{ ok: boolean }>(`/api/cook/foods/${id}`, { method: "DELETE" }),

  createOrder: (food_id: number, quantity: number, comment: string, payment_method: PaymentMethod) =>
    request<Order>("/api/orders", {
      method: "POST",
      body: JSON.stringify({ food_id, quantity, comment, payment_method }),
    }),
  getMyOrders: () => request<Order[]>("/api/orders"),
  getCookOrders: () => request<Order[]>("/api/cook/orders"),
  changeOrderStatus: (id: number, status: OrderStatus) =>
    request<Order>(`/api/orders/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }),
  cancelOrder: (id: number) => request<Order>(`/api/orders/${id}/cancel`, { method: "POST" }),
  confirmTonPayment: (id: number) =>
    request<Order>(`/api/orders/${id}/confirm-ton`, { method: "POST" }),

  createReview: (order_id: number, rating: number, text: string) =>
    request<Review>("/api/reviews", { method: "POST", body: JSON.stringify({ order_id, rating, text }) }),

  getFavoriteFoods: () => request<Food[]>("/api/favorites/foods"),
  getFavoriteCooks: () => request<Cook[]>("/api/favorites/cooks"),
  addFavoriteFood: (id: number) => request<{ ok: boolean }>(`/api/favorites/foods/${id}`, { method: "POST" }),
  removeFavoriteFood: (id: number) =>
    request<{ ok: boolean }>(`/api/favorites/foods/${id}`, { method: "DELETE" }),
  addFavoriteCook: (id: number) => request<{ ok: boolean }>(`/api/favorites/cooks/${id}`, { method: "POST" }),
  removeFavoriteCook: (id: number) =>
    request<{ ok: boolean }>(`/api/favorites/cooks/${id}`, { method: "DELETE" }),

  getSubscriptions: () => request<Cook[]>("/api/subscriptions"),
  subscribe: (cookId: number) => request<{ ok: boolean }>(`/api/subscriptions/${cookId}`, { method: "POST" }),
  unsubscribe: (cookId: number) =>
    request<{ ok: boolean }>(`/api/subscriptions/${cookId}`, { method: "DELETE" }),

  uploadPhoto: async (file: File): Promise<string> => {
    const form = new FormData();
    form.append("file", file);
    const result = await request<{ url: string }>("/api/upload", { method: "POST", body: form });
    return result.url;
  },
};

export function formatDistance(meters: number | null): string {
  if (meters == null) return "";
  if (meters < 1000) return `${Math.round(meters)} м`;
  return `${(meters / 1000).toFixed(1)} км`;
}

export function calcReferralDiscount(
  balance: number,
  gross: number,
  maxPercent: number,
): number {
  const g = Math.round(gross * 100) / 100;
  const bal = balance || 0;
  if (g <= 0 || bal <= 0) return 0;
  const cap = Math.round(g * (maxPercent / 100) * 100) / 100;
  const maxAllowed = Math.round(Math.max(g - 1, 0) * 100) / 100;
  return Math.round(Math.min(bal, cap, maxAllowed) * 100) / 100;
}

export function formatStars(amount: number): string {
  const n = Math.round(amount);
  return `${n.toLocaleString("ru-RU")} ⭐`;
}

export function formatTon(amount: number): string {
  return `${amount.toLocaleString("ru-RU", { maximumFractionDigits: 6 })} TON`;
}

/** @deprecated use formatStars */
export function formatPrice(price: number): string {
  return formatStars(price);
}
