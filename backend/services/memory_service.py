"""Память о пользователе: кратко, без лишнего текста, быстро из БД."""

from __future__ import annotations

import json
import logging
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User, UserMemory
from backend.utils.categories import categorize_text

logger = logging.getLogger(__name__)

_MAX_QUERIES = 6
_MAX_NOTE = 120


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
        parts.append(f"часто {top.lower()}")
    if user.diet_preference:
        parts.append(user.diet_preference.strip()[:50])
    if mem.prefers_cheap:
        parts.append("любите выгодное")
    if mem.orders_delivered >= 2:
        parts.append(f"{mem.orders_delivered} заказов")
    mem.companion_note = ", ".join(parts)[:_MAX_NOTE]


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
    if group and group != "Разное":
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


async def observe_order_delivered(
    session: AsyncSession,
    user: User,
    *,
    total_price: float,
    category: str,
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
    _refresh_note(mem, user)
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


async def clear_memory(session: AsyncSession, user_id: int) -> None:
    mem = await get_memory(session, user_id)
    mem.group_counts = "{}"
    mem.recent_queries = "[]"
    mem.last_group = None
    mem.last_category_path = None
    mem.companion_note = ""
    mem.searches_count = 0
    mem.prefers_cheap = False
    await session.commit()
