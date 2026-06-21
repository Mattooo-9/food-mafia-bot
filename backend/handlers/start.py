from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
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
            [KeyboardButton(text="👨‍🍳 Стать поваром")],
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


def _parse_ref(command: CommandObject | None) -> str | None:
    if not command or not command.args:
        return None
    arg = command.args.strip()
    if arg.startswith("ref_"):
        return arg[4:]
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    tg = message.from_user
    ref_code = _parse_ref(command)
    async with async_session_factory() as session:
        user, is_new = await user_service.get_or_create_user(
            session,
            TelegramUser(tg_id=tg.id, username=tg.username, first_name=tg.first_name),
            ref_code,
        )

    text = (
        f"Привет, {tg.first_name or 'друг'}! 👋\n\n"
        "<b>Еда Рядом</b> — домашняя еда от поваров рядом.\n\n"
        "🍲 Открой приложение — поиск, заказы, оплата, рейтинги.\n"
        "📍 Отправь геолокацию, чтобы видеть блюда рядом."
    )
    if user.referred_by_id and ref_code:
        text += f"\n\n🎁 Бонус {settings.referral_referee_bonus:.0f} ⭐ после первого заказа!"

    markup = webapp_keyboard()
    if markup is None:
        text += "\n\n⚠️ Mini App ещё не подключено."
        await message.answer(text, reply_markup=main_reply_keyboard())
        return
    await message.answer(text, reply_markup=markup)
    await message.answer("Быстрые действия:", reply_markup=main_reply_keyboard())


@router.message(Command("app"))
async def cmd_app(message: Message) -> None:
    markup = webapp_keyboard()
    if markup is None:
        await message.answer("Mini App ещё не подключено.")
        return
    await message.answer("Открыть приложение:", reply_markup=markup)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Справка</b>\n\n"
        "/start — меню\n"
        "/app — Mini App\n"
        "/become_cook — стать поваром\n\n"
        "📍 Геолокация — кнопка внизу или в профиле приложения.\n"
        "💳 Оплата — при заказе выбираете способ, расчёт при получении.\n"
        "🎁 Рефералы — в профиле приложения, бонусы обоим.\n"
        "⭐ Отзыв — после доставки в разделе «Заказы»."
    )
