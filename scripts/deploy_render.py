#!/usr/bin/env python3
"""Deploy food-mafia-bot to Render free tier via API.

Requires env RENDER_API_KEY (https://dashboard.render.com/u/settings#api-keys).
Other env: BOT_TOKEN, ADMIN_ID, WEBHOOK_SECRET (optional).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.render.com/v1"
REPO = "https://github.com/Mattooo-9/food-mafia-bot"
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
        detail = exc.read().decode()
        raise SystemExit(f"Render API {method} {path} -> {exc.code}: {detail}") from exc


def get_owner_id() -> str:
    owners = api("GET", "/owners")
    if not owners:
        raise SystemExit("No Render owners found")
    return owners[0]["owner"]["id"]


def find_service(owner_id: str) -> dict | None:
    services = api("GET", f"/services?ownerId={owner_id}&name={SERVICE_NAME}")
    for item in services:
        svc = item.get("service") or item
        if svc.get("name") == SERVICE_NAME:
            return svc
    return None


def create_service(owner_id: str) -> dict:
    body = {
        "type": "web_service",
        "name": SERVICE_NAME,
        "ownerId": owner_id,
        "repo": REPO,
        "branch": "main",
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "plan": "free",
            "region": "frankfurt",
            "healthCheckPath": "/health",
        },
    }
    result = api("POST", "/services", body)
    return result.get("service") or result


def set_env_vars(service_id: str) -> None:
    pairs = {
        "BOT_TOKEN": os.environ["BOT_TOKEN"],
        "ADMIN_ID": os.environ.get("ADMIN_ID", "0"),
        "USE_WEBHOOK": "1",
        "LOG_LEVEL": "INFO",
        "KEEP_ALIVE_INTERVAL_MINUTES": "10",
    }
    wh = os.environ.get("WEBHOOK_SECRET")
    if wh:
        pairs["WEBHOOK_SECRET"] = wh
    for key, value in pairs.items():
        api(
            "POST",
            f"/services/{service_id}/env-vars",
            {"envVar": {"key": key, "value": value}},
        )


def trigger_deploy(service_id: str) -> None:
    api("POST", f"/services/{service_id}/deploys", {"clearCache": False})


def main() -> None:
    if not os.environ.get("BOT_TOKEN"):
        raise SystemExit("BOT_TOKEN is not set")
    owner_id = get_owner_id()
    svc = find_service(owner_id)
    if svc is None:
        print("Creating Render service...")
        svc = create_service(owner_id)
    service_id = svc["id"]
    print(f"Service id: {service_id}")
    set_env_vars(service_id)
    trigger_deploy(service_id)
    url = svc.get("serviceDetails", {}).get("url") or f"https://{SERVICE_NAME}.onrender.com"
    print(f"Deploy triggered. URL (when ready): {url}")
    print("Mini App button will be set automatically on first successful start.")


if __name__ == "__main__":
    main()
