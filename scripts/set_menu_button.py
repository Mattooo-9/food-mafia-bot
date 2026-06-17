#!/usr/bin/env python3
"""Set Telegram menu button to settings.public_url (polling-friendly)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram.types import MenuButtonWebApp, WebAppInfo

from backend.bot_instance import bot
from backend.config import settings


async def main() -> None:
    url = settings.public_url
    if not url:
        raise SystemExit("WEBAPP_URL is not set")
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Еда Рядом", web_app=WebAppInfo(url=url))
        )
        await bot.delete_webhook(drop_pending_updates=False)
        print(f"Menu button -> {url} (webhook cleared for polling)")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
