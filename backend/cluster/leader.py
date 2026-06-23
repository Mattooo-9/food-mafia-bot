"""Распределённая блокировка лидера (Active-Passive) через Redis."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

import aiohttp

from backend.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_cluster: "ClusterManager | None" = None


class ClusterManager:
    def __init__(self) -> None:
        role = (settings.cluster_role or "auto").lower()
        if settings.instance_id:
            self.instance_id = settings.instance_id
        elif role == "primary":
            self.instance_id = "koyeb-primary"
        elif role == "standby":
            self.instance_id = "vercel-standby"
        else:
            self.instance_id = uuid.uuid4().hex[:12]
        self.role = role
        self._redis: Redis | None = None
        self._is_leader = False
        self._renew_task: asyncio.Task | None = None

    async def start(self) -> None:
        if not settings.redis_url:
            self._is_leader = self.role in ("primary", "auto")
            logger.warning(
                "REDIS_URL не задан — режим одного узла (лидер=%s)",
                self._is_leader,
            )
            return

        await self._connect_redis()
        if not self._redis:
            self._is_leader = self.role != "standby"
            return

        if self.role == "standby":
            await self._try_failover_if_peer_down()
        else:
            await self._acquire_or_wait()

        if self._is_leader and self.role != "standby":
            self._renew_task = asyncio.create_task(self._renew_loop())

    async def stop(self) -> None:
        if self._renew_task:
            self._renew_task.cancel()
            try:
                await self._renew_task
            except asyncio.CancelledError:
                pass
        if self._redis and self._is_leader:
            try:
                current = await self._redis.get(settings.lock_key)
                if current == self.instance_id:
                    await self._redis.delete(settings.lock_key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Release lock failed: %s", exc)
            await self._redis.aclose()

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    async def should_process_webhook(self) -> bool:
        if not settings.redis_url:
            return self.role != "standby"
        if not self._redis:
            await self._connect_redis()
        if not self._redis:
            return self.role != "standby"
        current = await self._redis.get(settings.lock_key)
        if current == self.instance_id:
            self._is_leader = True
            return True
        if self.role == "standby":
            await self._try_failover_if_peer_down()
            current = await self._redis.get(settings.lock_key)
            self._is_leader = current == self.instance_id
            return self._is_leader
        self._is_leader = False
        return False

    async def _connect_redis(self) -> None:
        if self._redis or not settings.redis_url:
            return
        try:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
            await self._redis.ping()
        except Exception as exc:  # noqa: BLE001
            logger.error("Redis connect failed: %s", exc)
            self._redis = None

    async def run_failover_check(self) -> dict:
        """Вызывается cron на standby (Vercel) каждую минуту."""
        if self.role != "standby":
            return {"action": "skip", "reason": "not standby"}
        peer_ok = await self._peer_healthy()
        if peer_ok:
            if self._is_leader:
                await self._release_lock()
                self._is_leader = False
            return {"action": "none", "peer": "healthy"}
        acquired = await self._acquire_lock()
        if acquired:
            self._is_leader = True
            if not self._renew_task or self._renew_task.done():
                self._renew_task = asyncio.create_task(self._renew_loop())
            return {"action": "failover", "leader": self.instance_id}
        return {"action": "wait", "leader": await self._current_leader()}

    async def _peer_healthy(self) -> bool:
        peer = settings.cluster_peer_url
        if not peer:
            return False
        url = peer.rstrip("/") + "/health"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status != 200:
                        return False
                    data = await resp.json()
                    return data.get("status") == "ok"
        except Exception:  # noqa: BLE001
            return False

    async def _current_leader(self) -> str | None:
        if not self._redis:
            return None
        return await self._redis.get(settings.lock_key)

    async def _acquire_lock(self) -> bool:
        if not self._redis:
            self._is_leader = True
            return True
        ok = await self._redis.set(
            settings.lock_key,
            self.instance_id,
            nx=True,
            ex=settings.lock_ttl_seconds,
        )
        if ok:
            self._is_leader = True
            logger.info("Лидер: %s", self.instance_id)
            return True
        current = await self._redis.get(settings.lock_key)
        if current == self.instance_id:
            self._is_leader = True
            return True
        self._is_leader = False
        return False

    async def _release_lock(self) -> None:
        if not self._redis:
            self._is_leader = False
            return
        current = await self._redis.get(settings.lock_key)
        if current == self.instance_id:
            await self._redis.delete(settings.lock_key)
        self._is_leader = False

    async def _acquire_or_wait(self) -> None:
        for attempt in range(8):
            if await self._acquire_lock():
                return
            await asyncio.sleep(min(2 ** attempt, 15))
        logger.error("Не удалось стать лидером за 8 попыток")

    async def _try_failover_if_peer_down(self) -> None:
        if await self._peer_healthy():
            self._is_leader = False
            return
        await self._acquire_lock()

    async def _renew_loop(self) -> None:
        while self._is_leader and self._redis:
            await asyncio.sleep(max(5, settings.lock_ttl_seconds // 3))
            try:
                current = await self._redis.get(settings.lock_key)
                if current != self.instance_id:
                    self._is_leader = False
                    logger.warning("Потеря лидерства")
                    break
                await self._redis.expire(settings.lock_key, settings.lock_ttl_seconds)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Renew lock failed: %s", exc)


def get_cluster() -> ClusterManager:
    global _cluster
    if _cluster is None:
        _cluster = ClusterManager()
    return _cluster
