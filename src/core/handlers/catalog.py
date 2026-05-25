from aiogram import Router, types, F
from aiogram.filters import Command
from ..services.user_service import user_service
import json

router = Router()

@router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    lang = user_service.get_user(message.from_user.id).get('lang', 'en')

    with open("data/items.json", "r") as f:
        items = json.load(f)

    # Example filtering by color (Rainbow spectrum)
    response = "🌈 Food Rainbow Catalog:\n\n"
    for item in items:
        response += f"{item['color_category']} - {item['name']} ({item['price']} TON)\n"

    await message.answer(response)
