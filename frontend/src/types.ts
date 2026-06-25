export type PaymentMethod = "STARS" | "TON" | "CASH" | "TRANSFER" | "CARD";
export type PaymentStatus = "PENDING" | "PAID";

export interface UserInsights {
  has_location: boolean;
  geo_label: string;
  meal_hint: string;
  memory_hint: string;
  summary: string;
  active_orders: number;
  open_wishes: number;
  claimed_wishes: number;
}

export interface User {
  id: number;
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
  wellness_consent: boolean;
  diet_preference: string | null;
  activity_level: string;
  language_code: string | null;
  locale: string;
  timezone: string | null;
  onboarding_done: boolean;
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

export interface SearchHistoryItem {
  id: number;
  query: string;
  scope: string;
  results_count: number;
  summary: string;
  created_at: string;
}

export interface AssistantGroup {
  title: string;
  subtitle: string | null;
  kind: string;
  foods: Food[];
  cooks: Cook[];
}

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

export interface FeedContext {
  meal: string;
  section_label: string;
  search_placeholder: string;
  season?: string;
  is_weekend?: boolean;
  calorie_summary?: string;
  meal_budget_label?: string;
  water_reminder?: string;
  harmony_hint?: string;
  rainbow_progress?: number;
}

export interface AssistantSearch {
  state: FeedState;
  has_location: boolean;
  activity: FeedActivity | null;
  context: FeedContext | null;
  message: string;
  companion: string;
  suggestions: string[];
  action: string | null;
  top_pick: { food_id: number; label: string } | null;
  intent: {
    category: string;
    feed: string;
    max_distance_m: number | null;
    price_max: number | null;
  };
  groups: AssistantGroup[];
  total_foods: number;
  total_cooks: number;
}

export interface CategoryGroup {
  group: string;
  categories: { name: string; subgroups: string[] }[];
}

export interface CategoriesResponse {
  groups: CategoryGroup[];
  flat: string[];
}

export interface CategorizeResult {
  group: string;
  category: string;
  subgroup: string | null;
  path: string;
  label: string;
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

export interface OrderWish {
  id: number;
  buyer_id: number;
  title: string;
  details: string;
  category_path: string | null;
  budget_max: number | null;
  portions: number;
  status: "OPEN" | "CLAIMED" | "COMPLETED" | "CANCELLED";
  cook_id: number | null;
  created_at: string;
  claimed_at: string | null;
  buyer_name: string | null;
  cook_name: string | null;
  distance_m: number | null;
}

export interface WellnessInfo {
  wellness_consent: boolean;
  diet_preference: string | null;
  activity_level: string;
  message: string;
  balance_hint: string;
  suggestion?: string;
  calorie_target: number;
  calories_today: number;
  calories_left: number;
  meal_budget: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  water_glasses: number;
  water_target: number;
  water_reminder: string;
  meal_schedule: string;
  harmony_hint: string;
  rainbow_progress: number;
  rainbow_missing: string[];
  rainbow: Record<string, number>;
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
