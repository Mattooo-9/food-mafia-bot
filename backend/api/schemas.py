from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models import FOOD_CATEGORIES, OrderStatus


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class CookProfileIn(BaseModel):
    cook_name: str | None = Field(default=None, min_length=2, max_length=128)
    cook_description: str | None = Field(default=None, max_length=2000)
    cook_photo: str | None = Field(default=None, max_length=512)
    is_online: bool | None = None


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
    price: float = Field(gt=0, le=1_000_000)
    category: str
    portions: int = Field(ge=0, le=1000)
    cooking_time_minutes: int = Field(default=30, ge=1, le=1440)
    photo: str | None = Field(default=None, max_length=512)


class FoodUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
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
    distance_m: float | None = None
    is_favorite: bool = False


class OrderIn(BaseModel):
    food_id: int
    quantity: int = Field(ge=1, le=100)
    comment: str = Field(default="", max_length=512)


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
    created_at: datetime
    food_name: str = ""
    food_photo: str | None = None
    cook_name: str | None = None
    buyer_name: str | None = None
    has_review: bool = False


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


class CategoriesOut(BaseModel):
    categories: list[str] = FOOD_CATEGORIES


class UploadOut(BaseModel):
    url: str


class OkOut(BaseModel):
    ok: bool = True
