from backend.api.schemas import UserOut
from backend.models import User


def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        has_location=user.lat is not None and user.lon is not None,
        is_cook=user.is_cook,
        cook_name=user.cook_name,
        cook_description=user.cook_description,
        cook_photo=user.cook_photo,
        is_online=user.is_online,
        rating_avg=user.rating_avg,
        rating_count=user.rating_count,
        referral_balance=user.referral_balance or 0.0,
        ton_wallet_address=user.ton_wallet_address,
        wellness_consent=bool(user.wellness_consent),
        diet_preference=user.diet_preference,
        activity_level=user.activity_level or "moderate",
        language_code=user.language_code,
        locale=user.locale or "en",
        timezone=user.timezone,
        onboarding_done=bool(user.onboarding_done),
    )
