import secrets

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.config import settings
from backend.database import async_session_factory
from backend.services import user_service
from backend.states import CookRegistration
from backend.utils.telegram_auth import TelegramUser

router = Router(name="cook")


@router.message(Command("become_cook"))
@router.message(F.text == "👨‍🍳 Стать поваром")
async def become_cook(message: Message, state: FSMContext) -> None:
    await state.set_state(CookRegistration.name)
    await message.answer(
        "👨‍🍳 Регистрация повара.\n\n"
        "Как будет называться ваша кухня? Например: «Кухня Марии».\n"
        "Для отмены отправьте /cancel"
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("Действие отменено.")


@router.message(CookRegistration.name, F.text)
async def cook_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 128:
        await message.answer("Название должно быть от 2 до 128 символов. Попробуйте ещё раз.")
        return
    await state.update_data(cook_name=name)
    await state.set_state(CookRegistration.description)
    await message.answer(
        "Отлично! Теперь коротко расскажите о себе и своей кухне.\n"
        "Если хотите пропустить — отправьте /skip"
    )


@router.message(CookRegistration.description, Command("skip"))
async def cook_description_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(cook_description="")
    await state.set_state(CookRegistration.photo)
    await message.answer("Пришлите фото профиля (или /skip, чтобы пропустить).")


@router.message(CookRegistration.description, F.text)
async def cook_description(message: Message, state: FSMContext) -> None:
    await state.update_data(cook_description=message.text.strip()[:2000])
    await state.set_state(CookRegistration.photo)
    await message.answer("Принято! Пришлите фото профиля (или /skip, чтобы пропустить).")


async def _finish_registration(message: Message, state: FSMContext, photo_url: str | None) -> None:
    data = await state.get_data()
    tg = message.from_user
    async with async_session_factory() as session:
        user = await user_service.get_or_create_user(
            session,
            TelegramUser(tg_id=tg.id, username=tg.username, first_name=tg.first_name),
        )
        await user_service.update_cook_profile(
            session,
            user,
            cook_name=data.get("cook_name"),
            cook_description=data.get("cook_description", ""),
            cook_photo=photo_url,
            is_online=True,
        )
    await state.clear()
    await message.answer(
        "🎉 Профиль повара создан!\n\n"
        "Теперь откройте Mini App (/app) → вкладка «Мои блюда», чтобы добавить блюда.\n"
        "Не забудьте отправить геолокацию 📍 — без неё покупатели не увидят вас в ленте «рядом»."
    )


@router.message(CookRegistration.photo, Command("skip"))
async def cook_photo_skip(message: Message, state: FSMContext) -> None:
    await _finish_registration(message, state, photo_url=None)


@router.message(CookRegistration.photo, F.photo)
async def cook_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    filename = f"cook_{message.from_user.id}_{secrets.token_hex(6)}.jpg"
    destination = settings.upload_dir / filename
    await message.bot.download(photo, destination=destination)
    await _finish_registration(message, state, photo_url=f"/uploads/{filename}")


@router.message(CookRegistration.photo)
async def cook_photo_invalid(message: Message) -> None:
    await message.answer("Пришлите именно фото или /skip, чтобы пропустить.")
