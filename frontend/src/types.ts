export type PaymentMethod = "CASH" | "TRANSFER" | "CARD";
export type PaymentStatus = "PENDING" | "PAID";

export interface User {
  id: number;
  tg_id: number;
  username: string | null;
  first_name: string | null;
  lat: number | null;
  lon: number | null;
  is_cook: boolean;
  cook_name: string | null;
  cook_description: string | null;
  cook_photo: string | null;
  is_online: boolean;
  rating_avg: number;
  rating_count: number;
}

export interface Food {
  id: number;
  cook_id: number;
  name: string;
  description: string;
  photo: string | null;
  price: number;
  category: string;
  portions: number;
  cooking_time_minutes: number;
  is_active: boolean;
  orders_count: number;
  created_at: string;
  cook_name: string | null;
  cook_rating: number;
  cook_is_online: boolean;
  distance_m: number | null;
  is_favorite: boolean;
}

export interface Cook {
  id: number;
  cook_name: string | null;
  first_name: string | null;
  cook_description: string | null;
  cook_photo: string | null;
  is_online: boolean;
  rating_avg: number;
  rating_count: number;
  distance_m: number | null;
  is_favorite: boolean;
  is_subscribed: boolean;
}

export type OrderStatus = "NEW" | "ACCEPTED" | "COOKING" | "READY" | "DELIVERED" | "CANCELLED";

export interface Order {
  id: number;
  buyer_id: number;
  cook_id: number;
  food_id: number;
  quantity: number;
  total_price: number;
  status: OrderStatus;
  comment: string;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  created_at: string;
  food_name: string;
  food_photo: string | null;
  cook_name: string | null;
  buyer_name: string | null;
  has_review: boolean;
}

export interface Review {
  id: number;
  rating: number;
  text: string;
  created_at: string;
  buyer_name: string | null;
}

export type FeedType = "nearby" | "new" | "popular" | "cheap" | "fast";

export interface FoodFilters {
  feed: FeedType;
  category: string | null;
  q: string;
  max_distance_m: number | null;
  price_min: number | null;
  price_max: number | null;
  min_rating: number | null;
}
