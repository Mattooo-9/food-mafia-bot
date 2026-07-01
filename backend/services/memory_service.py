"""Память о пользователе: обучение на поиске, заказах и избранном."""

from __future__ import annotations

import json
import logging
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserMemory
from backend.services.meal_context import build_meal_context
from backend.utils.categories import categorize_text

logger = logging.getLogger(__name__)

_MAX_QUERIES = 6
_MAX_NOTE = 120

_GROUP_CHIP: dict[str, str] = {
    "Горячие блюда": "Суп",
    "Закуски и салаты": "Салат",
    "Выпечка и сладкое": "Выпечка",
    "На каждый день": "Завтрак",
}


async def get_memory(session: AsyncSession, user_id: int) -> UserMemory:
    result = await session.execute(select(UserMemory).where(UserMemory.user_id == user_id))
    mem = result.scalar_one_or_none()
    if mem is None:
        mem = UserMemory(user_id=user_id)
        session.add(mem)
        await session.flush()
    return mem


def _loads_counts(raw: str) -> Counter[str]:
    try:
        data = json.loads(raw or "{}")
        if isinstance(data, dict):
            return Counter({str(k): int(v) for k, v in data.items()})
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return Counter()


def _loads_queries(raw: str) -> list[str]:
    try:
        data = json.loads(raw or "[]")
        if isinstance(data, list):
            return [str(q)[:80] for q in data if q][: _MAX_QUERIES]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _top_group(counts: Counter[str]) -> str | None:
    for group, _n in counts.most_common(3):
        if group and group != "Разное":
            return group
    return None


def _refresh_note(mem: UserMemory, user: User) -> None:
    parts: list[str] = []
    top = _top_group(_loads_counts(mem.group_counts))
    if top:
        chip = _GROUP_CHIP.get(top, top.lower())
        parts.append(chip)
    if user.diet_preference:
        parts.append(user.diet_preference.strip()[:40])
    mem.companion_note = " · ".join(parts)[:_MAX_NOTE]


async def observe_search(
    session: AsyncSession,
    user: User,
    query: str,
    *,
    category_hint: dict,
    results_count: int,
    price_max: float | None,
) -> None:
    q = query.strip()
    if not q:
        return
    mem = await get_memory(session, user.id)
    counts = _loads_counts(mem.group_counts)
    group = category_hint.get("group")
    if results_count > 0 and group and group != "Разное":
        counts[group] += 1
        mem.last_group = group
        mem.last_category_path = category_hint.get("path")
    recent = _loads_queries(mem.recent_queries)
    if not recent or recent[0] != q:
        recent.insert(0, q)
    mem.recent_queries = json.dumps(recent[:_MAX_QUERIES], ensure_ascii=False)
    mem.group_counts = json.dumps(dict(counts), ensure_ascii=False)
    mem.searches_count += 1
    if price_max or "дешев" in q.lower() or "недорог" in q.lower():
        mem.prefers_cheap = True
    _refresh_note(mem, user)
    await session.flush()


async def observe_favorite(
    session: AsyncSession,
    user: User,
    *,
    category: str,
) -> None:
    mem = await get_memory(session, user.id)
    cat = categorize_text(query=category)
    group = cat.get("group")
    if group and group != "Разное":
        counts = _loads_counts(mem.group_counts)
        counts[group] += 3
        mem.group_counts = json.dumps(dict(counts), ensure_ascii=False)
        mem.last_group = group
    _refresh_note(mem, user)
    await session.flush()


async def observe_order_delivered(
    session: AsyncSession,
    user: User,
    *,
    total_price: float,
    category: str,
    food_name: str = "",
    ingredients: str = "",
    portions: int = 1,
) -> None:
    mem = await get_memory(session, user.id)
    mem.orders_delivered += 1
    n = mem.orders_delivered
    mem.avg_order_stars = round(
        ((mem.avg_order_stars * (n - 1)) + total_price) / n,
        2,
    )
    cat = categorize_text(query=category)
    if cat.get("group") and cat["group"] != "Разное":
        counts = _loads_counts(mem.group_counts)
        counts[cat["group"]] += 2
        mem.group_counts = json.dumps(dict(counts), ensure_ascii=False)
        mem.last_group = cat["group"]
    _refresh_note(mem, user)
    if food_name:
        from backend.services.wellness_tracker import log_food_meal

        await log_food_meal(
            session,
            user,
            name=food_name,
            category=category,
            ingredients=ingredients,
            portions=portions,
        )
    await session.flush()


async def companion_line(session: AsyncSession, user: User) -> str:
    mem = await get_memory(session, user.id)
    if mem.companion_note:
        return mem.companion_note[:_MAX_NOTE]
    if user.diet_preference:
        return user.diet_preference[:_MAX_NOTE]
    return ""


async def preferred_groups(session: AsyncSession, user_id: int) -> list[str]:
    mem = await get_memory(session, user_id)
    counts = _loads_counts(mem.group_counts)
    return [g for g, _ in counts.most_common(3) if g != "Разное"]


async def enrich_intent(session: AsyncSession, user: User, intent: dict) -> dict:
    from backend.services.meal_context import apply_meal_to_intent
    from backend.services.search_history_service import weak_groups

    mem = await get_memory(session, user.id)
    raw = intent.get("query", "")
    counts = _loads_counts(mem.group_counts)
    memory_groups = [g for g, _ in counts.most_common(3) if g != "Разное"]

    ctx = build_meal_context(
        memory_groups=memory_groups,
        last_group=mem.last_group,
        user=user,
    )
    intent = apply_meal_to_intent(intent, ctx, has_query=bool(raw.strip()))

    weak = await weak_groups(session, user.id)
    if weak:
        intent["weak_groups"] = list(weak)

    if mem.prefers_cheap and intent.get("feed") == "nearby" and not intent.get("price_max"):
        intent["feed"] = "cheap"
        labels = intent.setdefault("sort_labels", [])
        if "выгодные" not in " ".join(labels):
            labels.insert(0, "выгодные")

    intent["recent_queries"] = _loads_queries(mem.recent_queries)
    intent["meal_context"] = ctx
    return intent


async def quick_suggestions(session: AsyncSession, user: User) -> list[str]:
    mem = await get_memory(session, user.id)
    memory_groups = [g for g, _ in _loads_counts(mem.group_counts).most_common(2) if g != "Разное"]
    ctx = build_meal_context(memory_groups=memory_groups, last_group=mem.last_group, user=user)

    out: list[str] = []
    seen: set[str] = set()

    def add(label: str) -> None:
        key = label.lower()
        if key not in seen and len(label) <= 24:
            seen.add(key)
            out.append(label)

    for q in _loads_queries(mem.recent_queries)[:2]:
        add(q)
    for chip in ctx.suggest_chips:
        add(chip)
    return out[:4]


async def clear_memory(session: AsyncSession, user_id: int) -> None:
    mem = await get_memory(session, user_id)
    mem.group_counts = "{}"
    mem.recent_queries = "[]"
    mem.last_group = None
    mem.last_category_path = None
    mem.companion_note = ""
    mem.searches_count = 0
    mem.prefers_cheap = False
    mem.wellness_state = "{}"
    await session.commit()
