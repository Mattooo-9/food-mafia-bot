import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request

from backend.api.app import create_app
from backend.cluster.leader import get_cluster
from backend.cluster.telegram_cloud import WEBHOOK_PATH, setup_webhook_safe, webhook_secret
from backend.cluster.watchdog import watchdog_loop
from backend.config import settings
from backend.database import init_db
from backend.handlers import create_dispatcher
from backend.utils.logging_config import setup_logging
from backend.bot_instance import bot

logger = logging.getLogger(__name__)

_dp: Dispatcher | None = None


def get_dispatcher() -> Dispatcher:
    global _dp
    if _dp is None:
        _dp = create_dispatcher()
    return _dp


def attach_webhook_route(app: FastAPI, dp: Dispatcher) -> None:
    @app.post(WEBHOOK_PATH, include_in_schema=False)
    async def telegram_webhook(request: Request) -> dict:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != webhook_secret():
            raise HTTPException(status_code=403, detail="Forbidden")
        cluster = get_cluster()
        if not await cluster.should_process_webhook():
            return {"ok": True, "skipped": "not-leader"}
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}


async def cloud_bot_setup() -> None:
    from backend.cluster.telegram_cloud import apply_menu_button

    await asyncio.sleep(2)
    cluster = get_cluster()
    await cluster.start()
    if cluster.is_leader:
        await apply_menu_button()
        if settings.use_webhook:
            await setup_webhook_safe()
    elif settings.cluster_role == "standby":
        logger.info("Standby node ready (failover via cron)")


async def run_api(app: FastAPI) -> None:
    import uvicorn

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    logger.info("API started on http://%s:%s [%s]", settings.host, settings.port, settings.cluster_role)
    await server.serve()


async def run_polling(dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot started (polling): @%s", me.username)
    await dp.start_polling(bot)


async def keep_alive_loop() -> None:
    import aiohttp

    interval = settings.keep_alive_interval_minutes * 60
    url = settings.public_url + "/health"
    while True:
        await asyncio.sleep(interval)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    logger.info("Keep-alive ping %s -> %s", url, resp.status)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Keep-alive ping failed: %s", exc)


async def ai_refresh_loop() -> None:
    from backend.database import async_session_factory
    from backend.services import ai_analyst_service

    await asyncio.sleep(15)
    while True:
        try:
            async with async_session_factory() as session:
                await ai_analyst_service.refresh_market_data(session)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI market refresh failed: %s", exc)
        await asyncio.sleep(max(60, settings.ai_refresh_interval_minutes * 60))


async def main() -> None:
    setup_logging()
    await init_db()

    app = create_app()
    dp = get_dispatcher()
    attach_webhook_route(app, dp)

    try:
        if settings.use_webhook and settings.public_url:
            tasks: list = [run_api(app), cloud_bot_setup(), ai_refresh_loop(), watchdog_loop()]
            if settings.keep_alive_interval_minutes > 0 and settings.cluster_role != "standby":
                tasks.append(keep_alive_loop())
            await asyncio.gather(*tasks)
        elif settings.use_webhook:
            logger.warning("USE_WEBHOOK=1, но публичный URL не задан — polling")
            await asyncio.gather(run_api(app), run_polling(dp), ai_refresh_loop())
        else:
            from backend.cluster.telegram_cloud import apply_menu_button

            await apply_menu_button()
            await asyncio.gather(run_api(app), run_polling(dp), ai_refresh_loop())
    finally:
        await get_cluster().stop()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Stopped")
