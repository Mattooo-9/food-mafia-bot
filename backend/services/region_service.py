"""Регион: валюта, способы оплаты, радиус — из языка и гео."""

from __future__ import annotations

from backend.config import settings
from backend.i18n.messages import normalize_locale, t
from backend.models import User

# Языки, где часто оплата при получении у домашних поваров
_CASH_LANGS = frozenset({"ru", "uk", "be", "kk", "uz", "ky", "tg", "az", "hy", "ka"})

# Регионы с ограничениями Telegram (подсказка прокси)
_RESTRICTED_LANGS = frozenset({"ru", "uk", "be", "kk", "uz", "ky", "tg", "fa"})


def region_for_user(user: User) -> dict:
    locale = normalize_locale(user.language_code, user.locale)
    lang = (user.language_code or locale or "en").split("-")[0].lower()

    payments = ["STARS", "TON"]
    if lang in _CASH_LANGS:
        payments.append("CASH")

    has_geo = user.lat is not None and user.lon is not None
    wish_radius_m = 25_000 if has_geo else 50_000
    search_radius_m = 10_000 if has_geo else 30_000

    return {
        "locale": locale,
        "language_code": user.language_code,
        "timezone": user.timezone,
        "currency": "XTR",
        "currency_label": "⭐",
        "ton_per_star": settings.ton_per_star,
        "payment_methods": payments,
        "wish_radius_m": wish_radius_m,
        "search_radius_m": search_radius_m,
        "telegram_proxy_hint": lang in _RESTRICTED_LANGS and bool(settings.telegram_api_base),
    }


def app_config(user: User) -> dict:
    from backend.i18n.messages import bundle_for

    region = region_for_user(user)
    return {
        "region": region,
        "strings": bundle_for(region["locale"]),
        "app_title": t(region["locale"], "app.title"),
    }
