from backend.api.schemas import CookOut, FoodOut, OrderOut, ReviewOut
from backend.models import Food, Order, Review, User


def serialize_food(
    food: Food,
    distance_m: float | None = None,
    favorite_ids: set[int] | None = None,
) -> FoodOut:
    out = FoodOut.model_validate(food)
    cook = food.cook
    out.cook_name = cook.cook_name or cook.first_name
    out.cook_rating = cook.rating_avg
    out.cook_is_online = cook.is_online
    out.distance_m = round(distance_m, 1) if distance_m is not None else None
    if favorite_ids is not None:
        out.is_favorite = food.id in favorite_ids
    return out


def serialize_cook(
    cook: User,
    distance_m: float | None = None,
    favorite_ids: set[int] | None = None,
    subscribed_ids: set[int] | None = None,
) -> CookOut:
    out = CookOut.model_validate(cook)
    out.distance_m = round(distance_m, 1) if distance_m is not None else None
    if favorite_ids is not None:
        out.is_favorite = cook.id in favorite_ids
    if subscribed_ids is not None:
        out.is_subscribed = cook.id in subscribed_ids
    return out


def serialize_order(order: Order, has_review: bool = False) -> OrderOut:
    out = OrderOut.model_validate(order)
    out.food_name = order.food.name
    out.food_photo = order.food.photo
    out.cook_name = order.cook.cook_name or order.cook.first_name
    out.buyer_name = order.buyer.first_name or order.buyer.username
    out.has_review = has_review
    return out


def serialize_review(review: Review) -> ReviewOut:
    out = ReviewOut.model_validate(review)
    out.buyer_name = review.buyer.first_name or review.buyer.username
    return out
