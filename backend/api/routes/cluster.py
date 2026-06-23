"""API маршруты кластера: health, failover cron."""

from fastapi import APIRouter, Header, HTTPException

from backend.cluster.leader import get_cluster
from backend.config import settings

router = APIRouter(tags=["cluster"])


@router.get("/cluster/status")
async def cluster_status() -> dict:
    cluster = get_cluster()
    return {
        "role": settings.cluster_role,
        "instance_id": cluster.instance_id,
        "is_leader": cluster.is_leader,
        "redis": bool(settings.redis_url),
        "peer": settings.cluster_peer_url or None,
        "public_url": settings.public_url or None,
    }


@router.api_route("/cluster/failover", methods=["GET", "POST"])
async def cluster_failover(
    authorization: str | None = Header(default=None),
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
) -> dict:
    secret = settings.cron_secret
    if secret:
        token = x_cron_secret or (authorization or "").removeprefix("Bearer ").strip()
        if token != secret:
            raise HTTPException(status_code=403, detail="Forbidden")
    cluster = get_cluster()
    await cluster.start()
    result = await cluster.run_failover_check()
    if result.get("action") == "failover":
        from backend.cluster.telegram_cloud import setup_webhook_safe

        await setup_webhook_safe()
    return result
