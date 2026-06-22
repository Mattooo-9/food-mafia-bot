"""Разбор запроса на естественном языке — без ручных фильтров."""

from __future__ import annotations

import re

from backend.utils.categories import categorize_text

_DIST_WORDS = ("рядом", "близко", "поблизости", "недалеко", "вокруг", "по соседству")
_CHEAP_WORDS = ("дешев", "недорог", "бюджет", "выгодн", "эконом")
_FAST_WORDS = ("быстр", "скор", "срочн")
_NEW_WORDS = ("нов", "свеж", "только что")
_POP_WORDS = ("популяр", "хит", "топ", "заказыва")
_QUALITY_WORDS = ("лучш", "рейтинг", "качеств", "вкусн")
_COOK_WORDS = ("повар", "кухн", "шеф", "готовит")


def parse_search_intent(query: str, *, has_location: bool) -> dict:
    raw = (query or "").strip()
    text = raw.lower()

    feed = "nearby"
    if any(w in text for w in _CHEAP_WORDS):
        feed = "cheap"
    elif any(w in text for w in _FAST_WORDS):
        feed = "fast"
    elif any(w in text for w in _NEW_WORDS):
        feed = "new"
    elif any(w in text for w in _POP_WORDS):
        feed = "popular"

    max_distance_m: float | None = None
    if any(w in text for w in _DIST_WORDS):
        max_distance_m = 5000.0
    km = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:км|km)\b", text)
    if km:
        max_distance_m = float(km.group(1).replace(",", ".")) * 1000
    meters = re.search(r"(\d+)\s*м(?:етр)?\b", text)
    if meters:
        max_distance_m = float(meters.group(1))

    price_max: float | None = None
    price_cap = re.search(r"до\s*(\d+)", text)
    if price_cap:
        price_max = float(price_cap.group(1))
    elif any(w in text for w in _CHEAP_WORDS):
        price_max = None

    min_rating: float | None = 4.0 if any(w in text for w in _QUALITY_WORDS) else None

    cat = categorize_text(query=raw)
    category: str | None = None
    if cat["group"] != "Разное" or cat["category"] != "Другое":
        category = cat["path"]

    wants_cooks = any(w in text for w in _COOK_WORDS)

    if has_location and max_distance_m is None and raw:
        max_distance_m = 8000.0
    if has_location and not raw:
        max_distance_m = 10000.0

    sort_labels = []
    if feed == "cheap":
        sort_labels.append("сначала выгодные")
    elif feed == "fast":
        sort_labels.append("быстрее готовят")
    elif feed == "popular":
        sort_labels.append("популярное")
    elif has_location:
        sort_labels.append("ближайшие")

    return {
        "query": raw,
        "feed": feed,
        "category": category,
        "category_hint": cat,
        "max_distance_m": max_distance_m,
        "price_max": price_max,
        "min_rating": min_rating,
        "wants_cooks": wants_cooks,
        "sort_labels": sort_labels,
    }
