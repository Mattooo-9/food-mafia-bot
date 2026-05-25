from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..services.user_service import user_service

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = user_service.get_user(message.from_user.id)

    if not user or not user.get('lang'):
        builder = InlineKeyboardBuilder()
        builder.button(text="🇺🇸 English", callback_data="set_lang_en")
        builder.button(text="🇷🇺 Русский", callback_data="set_lang_ru")
        await message.answer("Please choose your language / Пожалуйста, выберите язык:",
                             reply_markup=builder.as_markup())
    elif not user.get('location'):
        builder = InlineKeyboardBuilder()
        builder.row(types.KeyboardButton(text="📍 Share Location", request_location=True))
        await message.answer("Please share your location to find nearby chefs:",
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=builder.export(), resize_keyboard=True))
    else:
        # Mini App Launch Button (already in main logic)
        pass

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[2]
    user_service.update_user(callback.from_user.id, lang=lang)

    builder = InlineKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📍 Share Location" if lang == "en" else "📍 Отправить локацию",
                                     request_location=True))

    msg = "Great! Now please share your location:" if lang == "en" else "Отлично! Теперь отправьте вашу локацию:"
    await callback.message.answer(msg, reply_markup=types.ReplyKeyboardMarkup(keyboard=builder.export(), resize_keyboard=True))
    await callback.answer()

@router.message(F.location)
async def handle_location(message: types.Message):
    lang = user_service.get_user(message.from_user.id).get('lang', 'en')
    user_service.update_user(message.from_user.id, location={
        "lat": message.location.latitude,
        "lng": message.location.longitude
    })

    msg = "Setup complete! Type /start to open the marketplace." if lang == "en" else "Настройка завершена! Введите /start, чтобы открыть маркетплейс."
    await message.answer(msg, reply_markup=types.ReplyKeyboardRemove())
