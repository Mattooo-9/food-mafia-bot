from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from backend.config import settings
from backend.database import async_session_factory
from backend.services import user_service
from backend.utils.telegram_auth import TelegramUser

router = Router(name="start")


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="👨‍🍳 Стать поваром"), KeyboardButton(text="ℹ️ Помощь")],
        ],
    )


def webapp_keyboard() -> InlineKeyboardMarkup | None:
    if not settings.public_url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍲 Открыть Еда Рядом", web_app=WebAppInfo(url=settings.public_url))]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tg = message.from_user
    async with async_session_factory() as session:
        await user_service.get_or_create_user(
            session,
            TelegramUser(tg_id=tg.id, username=tg.username, first_name=tg.first_name),
        )

    text = (
        f"Привет, {tg.first_name or 'друг'}! 👋\n\n"
        "<b>Еда Рядом</b> — домашняя еда от поваров рядом с тобой.\n\n"
        "🍲 Открой приложение, чтобы посмотреть блюда поблизости.\n"
        "📍 Отправь геолокацию, чтобы мы показывали еду рядом.\n"
        "👨‍🍳 Хочешь готовить и продавать? Жми «Стать поваром»."
    )
    markup = webapp_keyboard()
    if markup is None:
        text += "\n\n⚠️ Mini App ещё не подключено: администратору нужно указать WEBAPP_URL в .env."
    await message.answer(text, reply_markup=main_reply_keyboard())
    if markup is not None:
        await message.answer("Открыть приложение:", reply_markup=markup)


@router.message(Command("app"))
async def cmd_app(message: Message) -> None:
    markup = webapp_keyboard()
    if markup is None:
        await message.answer("Mini App ещё не подключено: администратору нужно указать WEBAPP_URL в .env.")
        return
    await message.answer("Открыть приложение:", reply_markup=markup)


@router.message(Command("help"))
@router.message(lambda m: m.text == "ℹ️ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Команды бота:</b>\n\n"
        "/start — главное меню\n"
        "/app — открыть Mini App\n"
        "/become_cook — зарегистрироваться как повар\n\n"
        "📍 Отправьте геолокацию через кнопку, чтобы видеть еду рядом.\n"
        "🔔 Бот присылает уведомления о заказах и новых блюдах поваров, на которых вы подписаны."
    )
