export type PaymentMethod = "STARS" | "TON" | "CASH" | "TRANSFER" | "CARD";
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
  referral_balance: number;
  ton_wallet_address: string | null;
}

export interface ReferralInfo {
  balance: number;
  code: string;
  invited_count: number;
  link: string;
  max_discount_percent: number;
  referee_bonus: number;
  referrer_bonus: number;
}

export interface Food {
  id: number;
  cook_id: number;
  name: string;
  description: string;
  ingredients: string;
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
  cook_accepts_ton: boolean;
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

export interface TonPayment {
  wallet_address: string;
  amount_ton: number;
  comment: string;
}

export interface MarketInsight {
  category: string;
  dish_count: number;
  median_price: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  avg_rating: number;
  demand_index: number;
  competition_index: number;
  trend: string;
  trend_label: string;
  summary: string;
}

export interface MarketOverview {
  total_dishes: number;
  total_orders: number;
  avg_price: number;
  median_price: number;
  avg_rating: number;
  top_category: string;
  insights: MarketInsight[];
  analyst_note: string;
}

export interface PriceSuggestion {
  category: string;
  fair_price: number;
  suggested_price_min: number;
  suggested_price_max: number;
  verdict: string;
  verdict_label: string;
  price_score: number;
  summary: string;
  regional_avg_price: number;
  seasonal_market_price: number;
  season_name: string;
  season_factor: number;
  ingredient_cost: number;
  labor_cost: number;
  cook_minimum: number;
  cook_margin_percent: number;
  region_label: string;
  ingredient_items: string[];
  buyer_savings_hint: string;
  recommended_price: number;
  simple_message: string;
}

export interface FoodEvaluation {
  food_id: number;
  price_score: number;
  quality_score: number;
  demand_score: number;
  overall_score: number;
  verdict: string;
  verdict_label: string;
  fair_price: number;
  suggested_price_min: number;
  suggested_price_max: number;
  summary: string;
  buyer_tip: string;
  simple_tip?: string;
}

export interface Recommendation {
  food_id: number;
  food_name: string;
  food_photo: string | null;
  price: number;
  cook_name: string | null;
  distance_m: number | null;
  overall_score: number;
  buyer_tip: string;
  verdict_label: string;
}

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
  referral_discount: number;
  created_at: string;
  food_name: string;
  food_photo: string | null;
  cook_name: string | null;
  buyer_name: string | null;
  has_review: boolean;
  invoice_link: string | null;
  ton_payment: TonPayment | null;
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
