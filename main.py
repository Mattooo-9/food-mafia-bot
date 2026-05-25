import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from services.geo_service import GeoService
from utils.i18n import i18n

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://foodmafia.bot/app")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Simple session mock
user_sessions = {}

def get_lang(user_id):
    return user_sessions.get(user_id, {}).get('lang', 'en')

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_lang(message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.get('open_marketplace', lang), web_app=WebAppInfo(url=WEBAPP_URL)))
    builder.row(InlineKeyboardButton(text=i18n.get('buyer', lang), callback_data="role_buyer"))
    builder.row(InlineKeyboardButton(text=i18n.get('seller', lang), callback_data="role_chef"))

    await message.reply(
        i18n.get('welcome', lang),
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("role_"))
async def handle_role(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id)
    role = callback.data.split("_")[1]

    if role == "buyer":
        await callback.message.answer(i18n.get('buyer_welcome', lang))
    else:
        await callback.message.answer(i18n.get('chef_onboarding', lang))
    await callback.answer()

@dp.message(F.location)
async def handle_location(message: types.Message):
    lang = get_lang(message.from_user.id)
    lat = message.location.latitude
    lng = message.location.longitude
    h3_index = GeoService.get_h3_index(lat, lng)

    await message.reply(i18n.get('location_updated', lang, h3Index=h3_index))

@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.reply(i18n.get('matching_chef', lang))
    # Mock finding logic
    await message.reply("👨‍🍳 Nonna Maria\nSpecialty: Pasta")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
