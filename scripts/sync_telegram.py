#!/usr/bin/env python3
"""Sync Telegram menu button + webhook to the best available public URL."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

WEBHOOK_PATH = "/tg/webhook"


def sanitize_secret(raw: str) -> str:
    return "".join(c for c in raw if c.isalnum() or c in "_-")[:256]


def webhook_secret() -> str:
    raw = os.environ.get("WEBHOOK_SECRET", "")
    if not raw and os.environ.get("BOT_TOKEN"):
        raw = hashlib.sha256(os.environ["BOT_TOKEN"].encode()).hexdigest()[:32]
    return sanitize_secret(raw)


def tg(method: str, body: dict | None = None) -> dict:
    token = os.environ["BOT_TOKEN"]
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=data,
        method="POST" if data else "GET",
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def pick_url(env_key: str, fallback_key: str) -> str:
    direct = os.environ.get(env_key, "").strip().rstrip("/")
    if direct:
        return direct
    return os.environ.get(fallback_key, "").strip().rstrip("/")


def main() -> None:
    if not os.environ.get("BOT_TOKEN"):
        raise SystemExit("BOT_TOKEN required")

    # Mini App: stable Netlify/CDN URL if set, else primary backend.
    mini_app_url = pick_url("MINI_APP_URL", "SERVICE_URL")
    # Webhook: can be same host (proxied) or direct backend.
    webhook_base = pick_url("WEBHOOK_URL", "SERVICE_URL") or mini_app_url

    if not mini_app_url:
        raise SystemExit("MINI_APP_URL or SERVICE_URL required")

    menu = tg(
        "setChatMenuButton",
        {
            "menu_button": {
                "type": "web_app",
                "text": "Еда Рядом",
                "web_app": {"url": mini_app_url},
            }
        },
    )
    print("setChatMenuButton:", menu.get("ok"), menu.get("description", ""), "->", mini_app_url)

    use_webhook = os.environ.get("USE_WEBHOOK", "1") not in ("0", "false", "False")
    if use_webhook and webhook_base:
        secret = webhook_secret()
        wh = tg(
            "setWebhook",
            {
                "url": f"{webhook_base}{WEBHOOK_PATH}",
                "secret_token": secret,
                "drop_pending_updates": True,
            },
        )
        print("setWebhook:", wh.get("ok"), wh.get("description", ""), "->", webhook_base + WEBHOOK_PATH)
    else:
        wh = tg("deleteWebhook", {"drop_pending_updates": False})
        print("deleteWebhook (polling):", wh.get("ok"))

    info = tg("getWebhookInfo")
    print("webhook info:", json.dumps(info.get("result", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
