import asyncio
import logging

import uvicorn

from backend.api.app import create_app
from backend.bot_instance import bot
from backend.config import settings
from backend.database import init_db
from backend.handlers import create_dispatcher
from backend.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def run_bot() -> None:
    dp = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot started: @%s", me.username)
    await dp.start_polling(bot)


async def run_api() -> None:
    config = uvicorn.Config(
        create_app(),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    logger.info("API started on http://%s:%s", settings.host, settings.port)
    await server.serve()


async def main() -> None:
    setup_logging()
    await init_db()
    try:
        await asyncio.gather(run_api(), run_bot())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
