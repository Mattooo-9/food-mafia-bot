"""Язык и часовой пояс пользователя — без хранения лишних персональных данных."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# language_code (Telegram) → IANA timezone (приближение)
_LANG_TZ: dict[str, str] = {
    "ru": "Europe/Moscow",
    "uk": "Europe/Kyiv",
    "be": "Europe/Minsk",
    "kk": "Asia/Almaty",
    "uz": "Asia/Tashkent",
    "en": "UTC",
    "de": "Europe/Berlin",
    "fr": "Europe/Paris",
    "es": "Europe/Madrid",
    "it": "Europe/Rome",
    "tr": "Europe/Istanbul",
    "ar": "Asia/Riyadh",
    "fa": "Asia/Tehran",
    "he": "Asia/Jerusalem",
    "id": "Asia/Jakarta",
    "vi": "Asia/Ho_Chi_Minh",
    "th": "Asia/Bangkok",
    "zh": "Asia/Shanghai",
    "ja": "Asia/Tokyo",
    "ko": "Asia/Seoul",
    "pt": "Europe/Lisbon",
    "pl": "Europe/Warsaw",
}

_SUPPORTED_LOCALES = frozenset({"ru", "en"})


def normalize_locale(language_code: str | None, preferred: str | None = None) -> str:
    if preferred and preferred.split("-")[0].lower() in _SUPPORTED_LOCALES:
        return preferred.split("-")[0].lower()
    if language_code:
        base = language_code.split("-")[0].lower()
        if base in _SUPPORTED_LOCALES:
            return base
    return "ru"


def infer_timezone(
    *,
    timezone_name: str | None = None,
    language_code: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> str:
    if timezone_name:
        try:
            ZoneInfo(timezone_name)
            return timezone_name
        except (ZoneInfoNotFoundError, ValueError):
            pass
    if language_code:
        base = language_code.split("-")[0].lower()
        if base in _LANG_TZ:
            return _LANG_TZ[base]
    if lat is not None and lon is not None:
        return _tz_from_coords(lat, lon)
    return "UTC"


def zone_for_user(user):
    name = infer_timezone(
        timezone_name=getattr(user, "timezone", None),
        language_code=getattr(user, "language_code", None),
        lat=getattr(user, "lat", None),
        lon=getattr(user, "lon", None),
    )
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    lat = getattr(user, "lat", None)
    lon = getattr(user, "lon", None)
    if lat is not None and lon is not None:
        return _offset_from_lon(lon)
    return ZoneInfo("UTC")


def _offset_from_lon(lon: float):
    offset_hours = max(-12, min(14, round(lon / 15.0)))
    return timezone(timedelta(hours=offset_hours))


def _tz_from_coords(lat: float, lon: float) -> str:
    """Грубая оценка: сохраняем как UTC±N для последующего ZoneInfo/offset."""
    offset_hours = max(-12, min(14, round(lon / 15.0)))
    if offset_hours == 0:
        return "UTC"
    sign = "+" if offset_hours > 0 else ""
    return f"Etc/GMT{sign}{-offset_hours}"


def bounding_degrees(lat: float, radius_m: float) -> tuple[float, float]:
    dlat = radius_m / 111_320.0
    cos_lat = max(0.1, math.cos(math.radians(lat)))
    dlon = radius_m / (111_320.0 * cos_lat)
    return dlat, dlon


def fuzz_coordinate(value: float) -> float:
    """~150 м — достаточно для «рядом», без точного адреса."""
    return round(value, 3)
