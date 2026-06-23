#!/usr/bin/env python3
"""Switch Render web service to pull a pre-built Docker image (no build minutes)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.render.com/v1"
SERVICE_NAME = "food-mafia-bot"


def api(method: str, path: str, body: dict | None = None) -> dict:
    key = os.environ.get("RENDER_API_KEY")
    if not key:
        raise SystemExit("RENDER_API_KEY is not set")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Render API {method} {path} -> {exc.code}: {exc.read().decode()}") from exc


def find_service(owner_id: str) -> dict | None:
    services = api("GET", f"/services?ownerId={owner_id}&name={SERVICE_NAME}")
    for item in services:
        svc = item.get("service") or item
        if svc.get("name") == SERVICE_NAME:
            return svc
    return None


def service_url(svc: dict) -> str:
    details = svc.get("serviceDetails") or {}
    url = details.get("url")
    if url:
        return url if url.startswith("http") else f"https://{url}"
    return f"https://{svc.get('slug', SERVICE_NAME)}.onrender.com"


def main() -> None:
    image_path = os.environ.get("DOCKER_IMAGE")
    if not image_path:
        raise SystemExit("DOCKER_IMAGE is required (e.g. ghcr.io/owner/food-mafia-bot:latest)")

    owners = api("GET", "/owners")
    owner_id = owners[0]["owner"]["id"]
    svc = find_service(owner_id)
    if svc is None:
        raise SystemExit(f"Service {SERVICE_NAME} not found on Render")

    service_id = svc["id"]
    public_url = service_url(svc)

    api(
        "PATCH",
        f"/services/{service_id}",
        {
            "image": {
                "ownerId": owner_id,
                "imagePath": image_path,
            }
        },
    )
    print(f"Patched {service_id} -> {image_path}")

    pairs = {
        "BOT_TOKEN": os.environ["BOT_TOKEN"],
        "ADMIN_ID": os.environ.get("ADMIN_ID", "0"),
        "USE_WEBHOOK": "1",
        "WEBAPP_URL": public_url,
        "LOG_LEVEL": "INFO",
        "KEEP_ALIVE_INTERVAL_MINUTES": "10",
    }
    wh = os.environ.get("WEBHOOK_SECRET")
    if wh:
        pairs["WEBHOOK_SECRET"] = wh
    for key, value in pairs.items():
        api("PUT", f"/services/{service_id}/env-vars/{key}", {"value": value})

    cluster_env = {
        "CLUSTER_ROLE": "primary",
        "INSTANCE_ID": "render-primary",
    }
    redis = os.environ.get("REDIS_URL")
    peer = os.environ.get("CLUSTER_STANDBY_URL")
    if redis:
        cluster_env["REDIS_URL"] = redis
    if peer:
        cluster_env["CLUSTER_PEER_URL"] = peer
    cron = os.environ.get("CRON_SECRET")
    if cron:
        cluster_env["CRON_SECRET"] = cron
    for key, value in cluster_env.items():
        api("PUT", f"/services/{service_id}/env-vars/{key}", {"value": value})

    # Remove stale Postgres URL from old blueprint — use SQLite in container.
    try:
        api("DELETE", f"/services/{service_id}/env-vars/DATABASE_URL")
        print("Removed legacy DATABASE_URL (using SQLite in container)")
    except SystemExit:
        pass

    # deploy_only — pull image, no build
    deploy = api("POST", f"/services/{service_id}/deploys", {"deployMode": "deploy_only"})
    deploy_id = (deploy.get("deploy") or deploy).get("id")
    print(f"Deploy triggered (image pull): {public_url} deploy={deploy_id}")

    if deploy_id:
        import time

        for attempt in range(1, 37):
            info = api("GET", f"/services/{service_id}/deploys/{deploy_id}")
            status = (info.get("deploy") or info).get("status", "")
            print(f"deploy status: {status} ({attempt}/36)")
            if status == "live":
                break
            if status in ("build_failed", "update_failed", "canceled", "deactivated"):
                raise SystemExit(f"Render deploy failed: {status}")
            time.sleep(10)


if __name__ == "__main__":
    main()
