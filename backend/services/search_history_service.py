from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SearchHistory

_MAX_PER_USER = 40


async def record_search(
    session: AsyncSession,
    user_id: int,
    query: str,
    *,
    scope: str,
    results_count: int,
    summary: str,
) -> None:
    q = query.strip()
    if not q:
        return

    existing = await session.execute(
        select(SearchHistory)
        .where(
            SearchHistory.user_id == user_id,
            SearchHistory.query == q,
            SearchHistory.scope == scope,
        )
        .order_by(SearchHistory.created_at.desc())
        .limit(1)
    )
    row = existing.scalar_one_or_none()
    if row:
        row.results_count = results_count
        row.summary = summary[:500]
    else:
        session.add(
            SearchHistory(
                user_id=user_id,
                query=q,
                scope=scope,
                results_count=results_count,
                summary=summary[:500],
            )
        )

    await session.commit()

    ids = await session.execute(
        select(SearchHistory.id)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc())
        .offset(_MAX_PER_USER)
    )
    stale = [r[0] for r in ids.all()]
    if stale:
        await session.execute(delete(SearchHistory).where(SearchHistory.id.in_(stale)))
        await session.commit()


async def list_searches(session: AsyncSession, user_id: int, limit: int = 20) -> list[SearchHistory]:
    result = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def clear_searches(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(SearchHistory).where(SearchHistory.user_id == user_id))
    await session.commit()
