from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models import FOOD_CATEGORIES, OrderStatus, PaymentMethod


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class CookProfileIn(BaseModel):
    cook_name: str | None = Field(default=None, min_length=2, max_length=128)
    cook_description: str | None = Field(default=None, max_length=2000)
    cook_photo: str | None = Field(default=None, max_length=512)
    is_online: bool | None = None


class WalletIn(BaseModel):
    ton_wallet_address: str | None = Field(default=None, max_length=128)


class CurrencyOut(BaseModel):
    currency: str = "XTR"
    ton_per_star: float
    referral_unit: str = "stars"


class RegionOut(BaseModel):
    locale: str
    language_code: str | None = None
    timezone: str | None = None
    currency: str = "XTR"
    currency_label: str = "⭐"
    ton_per_star: float
    payment_methods: list[str]
    wish_radius_m: int
    search_radius_m: int
    telegram_proxy_hint: bool = False


class AppConfigOut(BaseModel):
    region: RegionOut
    strings: dict[str, str]
    app_title: str


class TonPaymentOut(BaseModel):
    wallet_address: str
    amount_ton: float
    comment: str


class UserOut(BaseModel):
    id: int
    username: str | None
    first_name: str | None
    has_location: bool = False
    is_cook: bool
    cook_name: str | None
    cook_description: str | None
    cook_photo: str | None
    is_online: bool
    rating_avg: float
    rating_count: int
    referral_balance: float = 0.0
    ton_wallet_address: str | None = None
    wellness_consent: bool = False
    diet_preference: str | None = None
    activity_level: str = "moderate"
    language_code: str | None = None
    locale: str = "ru"
    timezone: str | None = None
    onboarding_done: bool = False


class UserPreferencesIn(BaseModel):
    locale: str | None = Field(default=None, max_length=8)
    timezone: str | None = Field(default=None, max_length=64)


class UserInsightsOut(BaseModel):
    has_location: bool
    geo_label: str
    meal_hint: str
    memory_hint: str
    summary: str
    active_orders: int
    open_wishes: int
    claimed_wishes: int


class ReferralOut(BaseModel):
    balance: float
    code: str
    invited_count: int
    link: str
    max_discount_percent: int
    referee_bonus: float
    referrer_bonus: float


class CookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cook_name: str | None
    first_name: str | None
    cook_description: str | None
    cook_photo: str | None
    is_online: bool
    rating_avg: float
    rating_count: int
    distance_m: float | None = None
    is_favorite: bool = False
    is_subscribed: bool = False


class FoodIn(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: str = Field(default="", max_length=2000)
    ingredients: str = Field(default="", max_length=2000)
    price: float = Field(gt=0, le=1_000_000)
    category: str = Field(default="", max_length=256)
    portions: int = Field(ge=0, le=1000)
    cooking_time_minutes: int = Field(default=30, ge=1, le=1440)
    photo: str | None = Field(default=None, max_length=512)


class FoodUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    ingredients: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, gt=0, le=1_000_000)
    category: str | None = None
    portions: int | None = Field(default=None, ge=0, le=1000)
    cooking_time_minutes: int | None = Field(default=None, ge=1, le=1440)
    is_active: bool | None = None
    photo: str | None = Field(default=None, max_length=512)


class FoodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cook_id: int
    name: str
    description: str
    ingredients: str = ""
    photo: str | None
    price: float
    category: str
    portions: int
    cooking_time_minutes: int
    is_active: bool
    orders_count: int
    created_at: datetime
    cook_name: str | None = None
    cook_rating: float = 0.0
    cook_is_online: bool = False
    cook_accepts_ton: bool = False
    distance_m: float | None = None
    is_favorite: bool = False


class OrderIn(BaseModel):
    food_id: int
    quantity: int = Field(ge=1, le=100)
    comment: str = Field(default="", max_length=512)
    payment_method: PaymentMethod = PaymentMethod.STARS


class OrderStatusIn(BaseModel):
    status: OrderStatus


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    cook_id: int
    food_id: int
    quantity: int
    total_price: float
    status: str
    comment: str
    payment_method: str
    payment_status: str
    referral_discount: float = 0.0
    created_at: datetime
    food_name: str = ""
    food_photo: str | None = None
    cook_name: str | None = None
    buyer_name: str | None = None
    has_review: bool = False
    invoice_link: str | None = None
    ton_payment: TonPaymentOut | None = None


class ReviewIn(BaseModel):
    order_id: int
    rating: int = Field(ge=1, le=5)
    text: str = Field(default="", max_length=1000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    text: str
    created_at: datetime
    buyer_name: str | None = None


class CategoryItemOut(BaseModel):
    name: str
    subgroups: list[str]


class CategoryGroupOut(BaseModel):
    group: str
    categories: list[CategoryItemOut]


class CategoriesOut(BaseModel):
    groups: list[CategoryGroupOut]
    flat: list[str] = FOOD_CATEGORIES


class CategorizeOut(BaseModel):
    group: str
    category: str
    subgroup: str | None
    path: str
    label: str


class AssistantIntentOut(BaseModel):
    category: str
    feed: str
    max_distance_m: float | None
    price_max: float | None


class AssistantGroupOut(BaseModel):
    title: str
    subtitle: str | None = None
    kind: str
    foods: list[FoodOut] = []
    cooks: list[CookOut] = []


class AssistantTopPickOut(BaseModel):
    food_id: int
    label: str


class FeedActivityOut(BaseModel):
    active_orders: int = 0
    open_wishes: int = 0
    claimed_wishes: int = 0


class FeedContextOut(BaseModel):
    meal: str
    section_label: str
    search_placeholder: str
    season: str = ""
    is_weekend: bool = False
    calorie_summary: str = ""
    meal_budget_label: str = ""
    water_reminder: str = ""
    harmony_hint: str = ""
    rainbow_progress: int = 0


class AssistantSearchOut(BaseModel):
    state: str = "browse"
    has_location: bool = False
    activity: FeedActivityOut | None = None
    context: FeedContextOut | None = None
    message: str = ""
    companion: str = ""
    suggestions: list[str] = []
    action: str | None = None
    top_pick: AssistantTopPickOut | None = None
    intent: AssistantIntentOut
    groups: list[AssistantGroupOut]
    total_foods: int
    total_cooks: int


class SearchHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    scope: str
    results_count: int
    summary: str
    created_at: datetime


class UploadOut(BaseModel):
    url: str


class OkOut(BaseModel):
    ok: bool = True


class MarketInsightOut(BaseModel):
    category: str
    dish_count: int
    median_price: float
    avg_price: float
    min_price: float
    max_price: float
    avg_rating: float
    demand_index: float
    competition_index: float
    trend: str
    trend_label: str
    summary: str


class MarketOverviewOut(BaseModel):
    total_dishes: int
    total_orders: int
    avg_price: float
    median_price: float
    avg_rating: float
    top_category: str
    insights: list[MarketInsightOut]
    analyst_note: str


class PriceSuggestionOut(BaseModel):
    category: str
    fair_price: float
    suggested_price_min: float
    suggested_price_max: float
    verdict: str
    verdict_label: str
    price_score: int
    summary: str
    regional_avg_price: float
    seasonal_market_price: float
    season_name: str
    season_factor: float
    ingredient_cost: float
    labor_cost: float
    cook_minimum: float
    cook_margin_percent: float
    region_label: str
    ingredient_items: list[str]
    buyer_savings_hint: str
    recommended_price: int
    simple_message: str


class FoodEvaluationOut(BaseModel):
    food_id: int
    price_score: int
    quality_score: int
    demand_score: int
    overall_score: int
    verdict: str
    verdict_label: str
    fair_price: float
    suggested_price_min: float
    suggested_price_max: float
    summary: str
    buyer_tip: str
    simple_tip: str = ""


class RecommendationOut(BaseModel):
    food_id: int
    food_name: str
    food_photo: str | None
    price: float
    cook_name: str | None
    distance_m: float | None
    overall_score: int
    buyer_tip: str
    verdict_label: str


class OrderWishIn(BaseModel):
    title: str = Field(min_length=2, max_length=128)
    details: str = Field(default="", max_length=2000)
    budget_max: float | None = Field(default=None, ge=0)
    portions: int = Field(default=1, ge=1, le=100)


class OrderWishOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    title: str
    details: str
    category_path: str | None
    budget_max: float | None
    portions: int
    status: str
    cook_id: int | None
    created_at: datetime
    claimed_at: datetime | None = None
    buyer_name: str | None = None
    cook_name: str | None = None
    distance_m: float | None = None


class WellnessIn(BaseModel):
    consent: bool | None = None
    diet_preference: str | None = Field(default=None, max_length=256)
    activity_level: str | None = Field(default=None, max_length=16)


class WellnessOut(BaseModel):
    wellness_consent: bool
    diet_preference: str | None = None
    activity_level: str = "moderate"
    message: str = ""
    balance_hint: str = ""
    suggestion: str = ""
    calorie_target: int = 0
    calories_today: int = 0
    calories_left: int = 0
    meal_budget: int = 0
    protein_g: int = 0
    carbs_g: int = 0
    fat_g: int = 0
    water_glasses: int = 0
    water_target: int = 8
    water_reminder: str = ""
    meal_schedule: str = ""
    harmony_hint: str = ""
    rainbow_progress: int = 0
    rainbow_missing: list[str] = []
    rainbow: dict[str, int] = {}


class RecipeHintsOut(BaseModel):
    hints: list[str]
