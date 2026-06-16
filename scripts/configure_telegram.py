#!/usr/bin/env python3
"""After Render deploy: set Telegram menu button + webhook to production URL."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SERVICE_URL = os.environ.get("SERVICE_URL", "https://food-mafia-bot.onrender.com").rstrip("/")
WEBHOOK_PATH = "/tg/webhook"


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


def main() -> None:
    if not os.environ.get("BOT_TOKEN"):
        raise SystemExit("BOT_TOKEN required")
    menu = tg(
        "setChatMenuButton",
        {
            "menu_button": {
                "type": "web_app",
                "text": "🍲 Еда Рядом",
                "web_app": {"url": SERVICE_URL},
            }
        },
    )
    print("setChatMenuButton:", menu.get("ok"), menu.get("description", ""))
    wh_secret = os.environ.get("WEBHOOK_SECRET", "")
    webhook_url = f"{SERVICE_URL}{WEBHOOK_PATH}"
    params = {"url": webhook_url, "drop_pending_updates": True}
    if wh_secret:
        params["secret_token"] = wh_secret
    wh = tg("setWebhook", params)
    print("setWebhook:", wh.get("ok"), wh.get("description", ""))
    info = tg("getWebhookInfo")
    print("webhook:", info.get("result", {}))


if __name__ == "__main__":
    main()
