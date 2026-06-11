import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(Exception):
    """Raised when Telegram WebApp init data is invalid."""


@dataclass
class TelegramUser:
    tg_id: int
    username: str | None
    first_name: str | None


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> TelegramUser:
    """Validate Telegram Mini App initData string (HMAC-SHA256 per Telegram docs)."""
    if not init_data:
        raise InitDataError("Empty init data")

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError as exc:
        raise InitDataError("Malformed init data") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("Missing hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise InitDataError("Hash mismatch")

    auth_date = int(pairs.get("auth_date", "0"))
    if auth_date <= 0 or time.time() - auth_date > max_age_seconds:
        raise InitDataError("Init data expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("Missing user")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("Malformed user payload") from exc

    tg_id = user.get("id")
    if not isinstance(tg_id, int):
        raise InitDataError("Missing user id")

    return TelegramUser(
        tg_id=tg_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
    )
