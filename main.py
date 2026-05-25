import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://food-mafia-bot.onrender.com")
PORT = int(os.environ.get('PORT', 8080))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Open Food Mafia 🍔",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))

    await message.reply(
        "Welcome to the new Food Mafia. Your interactive P2P marketplace on TON.",
        reply_markup=builder.as_markup()
    )

async def handle_index(request):
    return web.FileResponse('./webapp/dist/index.html')

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)

    # Serve built assets
    dist_path = os.path.join(os.path.dirname(__file__), 'webapp/dist')
    if os.path.exists(dist_path):
        app.router.add_static('/', dist_path)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
