from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from backend.config import settings

_session: AiohttpSession | None = None
if settings.telegram_api_base.strip():
    _session = AiohttpSession(api=TelegramAPIServer.from_base(settings.telegram_api_base.strip()))

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=_session,
)
