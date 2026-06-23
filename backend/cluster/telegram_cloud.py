"""Настройка Telegram webhook и меню (общее для primary/standby)."""

from __future__ import annotations

import hashlib
import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from backend.bot_info import set_bot_username
from backend.bot_instance import bot
from backend.config import settings

logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/tg/webhook"


def webhook_secret() -> str:
    raw = settings.webhook_secret or hashlib.sha256(settings.bot_token.encode()).hexdigest()[:32]
    return "".join(c for c in raw if c.isalnum() or c in "_-")[:256]


async def apply_menu_button() -> None:
    public_url = settings.public_url
    if not public_url:
        logger.warning("WEBAPP_URL is not set — Mini App button is not configured")
        return
    try:
        me = await bot.get_me()
        if me.username:
            set_bot_username(me.username)
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Главное меню"),
                BotCommand(command="app", description="Открыть приложение"),
                BotCommand(command="become_cook", description="Стать поваром"),
                BotCommand(command="help", description="Справка"),
            ]
        )
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Еда Рядом", web_app=WebAppInfo(url=public_url))
        )
        logger.info("Mini App menu button set to %s", public_url)
    except TelegramAPIError as exc:
        logger.error("Failed to set menu button: %s", exc)


async def setup_webhook() -> None:
    url = settings.public_url + WEBHOOK_PATH
    await bot.set_webhook(url=url, secret_token=webhook_secret(), drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot started (webhook): @%s -> %s", me.username, url)


async def setup_webhook_safe() -> None:
    if not settings.public_url:
        return
    try:
        await setup_webhook()
    except TelegramAPIError as exc:
        logger.error("Webhook setup failed: %s", exc)
