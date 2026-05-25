import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiohttp import web

# Import core modular router
from src.core.router import get_main_router
from src.core.services.user_service import user_service

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://food-mafia-bot.onrender.com")
PORT = int(os.environ.get('PORT', 8080))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Attach the main core router
dp.include_router(get_main_router())

@dp.message(Command("start"))
async def cmd_start_main(message: types.Message):
    user = user_service.get_user(message.from_user.id)

    # If onboarding is not complete, the onboarding handler (via router) will take over
    if not user or not user.get('lang') or not user.get('location'):
        return # Handled by onboarding.py router

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Launch Food Mafia 🍔",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))

    await message.reply(
        "Welcome to the new Food Mafia. Your interactive P2P marketplace on TON.",
        reply_markup=builder.as_markup()
    )

# Web handlers
async def handle_index(request):
    return web.FileResponse('./webapp/index.html')

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)

    webapp_path = os.path.join(os.path.dirname(__file__), 'webapp')
    if os.path.exists(webapp_path):
        app.router.add_static('/', webapp_path)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

async def main():
    logging.info("Starting Scalable Food Mafia Bot...")
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
