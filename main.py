import asyncio
import hashlib
import logging

import uvicorn
from aiogram import Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import MenuButtonWebApp, Update, WebAppInfo
from fastapi import FastAPI, HTTPException, Request

from backend.api.app import create_app
from backend.bot_instance import bot
from backend.config import settings
from backend.database import init_db
from backend.handlers import create_dispatcher
from backend.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/tg/webhook"


def webhook_secret() -> str:
    if settings.webhook_secret:
        return settings.webhook_secret
    return hashlib.sha256(settings.bot_token.encode()).hexdigest()[:32]


def attach_webhook_route(app: FastAPI, dp: Dispatcher) -> None:
    @app.post(WEBHOOK_PATH, include_in_schema=False)
    async def telegram_webhook(request: Request) -> dict:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != webhook_secret():
            raise HTTPException(status_code=403, detail="Forbidden")
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}


async def apply_menu_button() -> None:
    """Point the bot menu button at the Mini App (no BotFather needed)."""
    public_url = settings.public_url
    if not public_url:
        logger.warning("WEBAPP_URL is not set — Mini App button is not configured")
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Еда Рядом", web_app=WebAppInfo(url=public_url)
            )
        )
        logger.info("Mini App menu button set to %s", public_url)
    except TelegramAPIError as exc:
        logger.error("Failed to set menu button: %s", exc)


async def run_api(app: FastAPI) -> None:
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    logger.info("API started on http://%s:%s", settings.host, settings.port)
    await server.serve()


async def run_polling(dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot started (polling): @%s", me.username)
    await dp.start_polling(bot)


async def setup_webhook() -> None:
    url = settings.public_url + WEBHOOK_PATH
    await bot.set_webhook(url=url, secret_token=webhook_secret(), drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot started (webhook): @%s -> %s", me.username, url)


async def keep_alive_loop() -> None:
    """Ping our own public URL so free-tier hosting never goes to sleep."""
    import aiohttp

    interval = settings.keep_alive_interval_minutes * 60
    url = settings.public_url + "/health"
    while True:
        await asyncio.sleep(interval)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    logger.info("Keep-alive ping %s -> %s", url, resp.status)
        except Exception as exc:  # noqa: BLE001 — never let the loop die
            logger.warning("Keep-alive ping failed: %s", exc)


async def main() -> None:
    setup_logging()
    await init_db()

    app = create_app()
    dp = create_dispatcher()
    attach_webhook_route(app, dp)

    await apply_menu_button()

    try:
        if settings.use_webhook and settings.public_url:
            await setup_webhook()
            tasks = [run_api(app)]
            if settings.keep_alive_interval_minutes > 0:
                tasks.append(keep_alive_loop())
            await asyncio.gather(*tasks)
        else:
            if settings.use_webhook:
                logger.warning("USE_WEBHOOK=1, но публичный URL не задан — запускаю polling")
            await asyncio.gather(run_api(app), run_polling(dp))
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
