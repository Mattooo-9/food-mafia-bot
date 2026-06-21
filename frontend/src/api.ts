import { getInitData } from "./telegram";
import type { Cook, Food, FoodFilters, Order, OrderStatus, PaymentMethod, Review, User } from "./types";

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
  setLocation: (lat: number, lon: number) =>
    request<User>("/api/me/location", { method: "POST", body: JSON.stringify({ lat, lon }) }),
  updateCookProfile: (data: {
    cook_name?: string;
    cook_description?: string;
    cook_photo?: string;
    is_online?: boolean;
  }) => request<User>("/api/me/cook-profile", { method: "POST", body: JSON.stringify(data) }),
  getCategories: () => request<{ categories: string[] }>("/api/categories"),

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

export function formatPrice(price: number): string {
  return `${price.toLocaleString("ru-RU", { maximumFractionDigits: 2 })} ₽`;
}
