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


class TonPaymentOut(BaseModel):
    wallet_address: str
    amount_ton: float
    comment: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_id: int
    username: str | None
    first_name: str | None
    lat: float | None
    lon: float | None
    is_cook: bool
    cook_name: str | None
    cook_description: str | None
    cook_photo: str | None
    is_online: bool
    rating_avg: float
    rating_count: int
    referral_balance: float = 0.0
    ton_wallet_address: str | None = None


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
