from aiogram import F, Router
from aiogram.types import Message

from backend.database import async_session_factory
from backend.services import user_service
from backend.utils.telegram_auth import TelegramUser

router = Router(name="location")


@router.message(F.location)
async def handle_location(message: Message) -> None:
    tg = message.from_user
    location = message.location
    async with async_session_factory() as session:
        user, _ = await user_service.get_or_create_user(
            session,
            TelegramUser(tg_id=tg.id, username=tg.username, first_name=tg.first_name),
        )
        await user_service.update_location(session, user, location.latitude, location.longitude)
    await message.answer(
        "📍 Геолокация сохранена! Теперь в приложении вы увидите еду и поваров рядом."
    )
