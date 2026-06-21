import logging
import secrets

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.bot_info import get_bot_username
from backend.config import settings
from backend.models import Order, OrderStatus, User

logger = logging.getLogger(__name__)


def _generate_code() -> str:
    return secrets.token_hex(4).upper()


async def ensure_referral_code(session: AsyncSession, user: User) -> str:
    if user.referral_code:
        return user.referral_code
    for _ in range(12):
        code = _generate_code()
        user.referral_code = code
        try:
            await session.commit()
            return code
        except IntegrityError:
            await session.rollback()
            user = await session.get(User, user.id)
            if user is None:
                raise
            if user.referral_code:
                return user.referral_code
    raise RuntimeError("Could not generate unique referral code")


async def attach_referrer(session: AsyncSession, user: User, ref_code: str) -> bool:
    """Link user to referrer once. Returns True if attached."""
    if user.referred_by_id is not None or not ref_code:
        return False
    code = ref_code.strip().upper()
    if not code or user.referral_code == code:
        return False
    result = await session.execute(select(User).where(User.referral_code == code))
    referrer = result.scalar_one_or_none()
    if referrer is None or referrer.id == user.id:
        return False
    user.referred_by_id = referrer.id
    await session.commit()
    logger.info("User %s referred by %s (code %s)", user.id, referrer.id, code)
    return True


async def get_invited_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(User).where(User.referred_by_id == user_id)
    )
    return int(result.scalar_one())


def build_referral_link(code: str) -> str:
    username = get_bot_username()
    if not username:
        return f"https://t.me/?start=ref_{code}"
    return f"https://t.me/{username}?start=ref_{code}"


async def get_referral_info(session: AsyncSession, user: User) -> dict:
    code = await ensure_referral_code(session, user)
    return {
        "code": code,
        "link": build_referral_link(code),
        "balance": round(user.referral_balance or 0, 2),
        "invited_count": await get_invited_count(session, user.id),
        "referrer_bonus": settings.referral_referrer_bonus,
        "referee_bonus": settings.referral_referee_bonus,
        "max_discount_percent": int(settings.referral_max_discount_rate * 100),
    }


def calc_referral_discount(buyer: User, gross: float) -> float:
    gross = round(gross, 2)
    balance = buyer.referral_balance or 0
    if gross <= 0 or balance <= 0:
        return 0.0
    cap = round(gross * settings.referral_max_discount_rate, 2)
    max_allowed = round(max(gross - 1.0, 0.0), 2)
    return round(min(balance, cap, max_allowed), 2)


def apply_referral_discount(buyer: User, gross: float) -> float:
    discount = calc_referral_discount(buyer, gross)
    if discount > 0:
        buyer.referral_balance = round((buyer.referral_balance or 0) - discount, 2)
    return discount


async def restore_referral_discount(session: AsyncSession, buyer: User, discount: float) -> None:
    if discount > 0:
        buyer.referral_balance = round((buyer.referral_balance or 0) + discount, 2)


async def on_order_delivered(session: AsyncSession, order: Order) -> tuple[User, User | None, float, float] | None:
    """First delivery: referral bonuses. Returns notify payload or None."""
    buyer = await session.get(User, order.buyer_id)
    if buyer is None or buyer.referral_welcome_claimed:
        return None

    buyer.referral_welcome_claimed = True

    if not buyer.referred_by_id:
        return None

    buyer.referral_balance = round(
        (buyer.referral_balance or 0) + settings.referral_referee_bonus, 2
    )

    referrer: User | None = await session.get(User, buyer.referred_by_id)
    if referrer and referrer.id != buyer.id:
        referrer.referral_balance = round(
            (referrer.referral_balance or 0) + settings.referral_referrer_bonus, 2
        )
    else:
        referrer = None

    logger.info(
        "Referral rewards: buyer=%s referrer=%s",
        buyer.id,
        referrer.id if referrer else None,
    )
    return (buyer, referrer, settings.referral_referee_bonus, settings.referral_referrer_bonus)
