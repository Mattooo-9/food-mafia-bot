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
    # Main and ONLY button to launch the Mini App
    builder.row(InlineKeyboardButton(
        text="Launch Food Mafia 🍔",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))

    await message.reply(
        "Welcome to Food Mafia. Your anonymous P2P marketplace on TON.",
        reply_markup=builder.as_markup()
    )

# Web handlers
async def handle_index(request):
    # Explicitly serve index.html
    return web.FileResponse('./webapp/index.html')

async def handle_health(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()

    # Route for the main page
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', handle_health)

    # Serve other static files (css, js, manifest)
    webapp_path = os.path.join(os.path.dirname(__file__), 'webapp')
    if os.path.exists(webapp_path):
        app.router.add_static('/', webapp_path)
        logging.info(f"Serving static files from {webapp_path}")
    else:
        logging.warning(f"Webapp path {webapp_path} not found!")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

async def main():
    logging.info("Starting bot and web server...")
    # Run bot polling and web server concurrently
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
