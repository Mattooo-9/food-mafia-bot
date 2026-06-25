"""Интерактивное сопровождение в чате — только факты и действия."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.database import async_session_factory
from backend.handlers.start import webapp_keyboard
from backend.services import user_service
from backend.services.meal_context import build_meal_context
from backend.utils.categories import categorize_text
from backend.utils.telegram_auth import TelegramUser

router = Router(name="guide")

_GUIDE_KEYWORDS: dict[tuple[str, ...], str] = {
    ("суп", "борщ", "бульон", "щи", "уха"): (
        "Откройте приложение и введите «суп» в поиске."
    ),
    ("салат", "закуск"): (
        "Откройте приложение — раздел поиска или «Салат» в быстрых фильтрах."
    ),
    ("заказ", "хочу", "нужно", "голод", "поесть"): (
        "Готовое — в ленте. Если нет подходящего — «Запрос поварам» в заказах."
    ),
    ("повар", "готов", "кухн"): (
        "Регистрация повара: /become_cook. Заказы — в «Моей кухне»."
    ),
    ("помощ", "как", "что делать"): (
        "1) Геолокация  2) Поиск по блюду  3) Заказ или запрос поварам"
    ),
}


def _match_guide(text: str) -> str | None:
    low = text.lower()
    for keys, reply in _GUIDE_KEYWORDS.items():
        if any(k in low for k in keys):
            return reply
    return None


async def _send_onboarding_steps(message: Message, first_name: str | None) -> None:
    await asyncio.sleep(1.2)
    steps = (
        "Как пользоваться:\n\n"
        "Геолокация — сортировка по расстоянию\n"
        "Поиск — по названию или категории\n"
        "Запрос поварам — если нет готового блюда"
    )
    await message.answer(steps, reply_markup=webapp_keyboard())


@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def guide_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        return
    reply = _match_guide(text)
    tg = message.from_user
    user = None
    if tg:
        async with async_session_factory() as session:
            user, _ = await user_service.get_or_create_user(
                session,
                TelegramUser(
                    tg_id=tg.id,
                    username=tg.username,
                    first_name=tg.first_name,
                    language_code=tg.language_code,
                ),
            )
    if not reply:
        cat = categorize_text(query=text)
        if cat.get("score", 0) >= 1 and cat["group"] != "Разное":
            reply = f"Категория: {cat['label']}. Повторите в поиске приложения."
        else:
            ctx = build_meal_context(user=user)
            chip = ctx.suggest_chips[0] if ctx.suggest_chips else "Обед"
            reply = (
                f"Сейчас — {ctx.section_label.lower()}. "
                f"Откройте приложение: «{chip}» или свой запрос."
            )

    await message.answer(reply, reply_markup=webapp_keyboard())


async def schedule_new_user_guide(message: Message, first_name: str | None) -> None:
    asyncio.create_task(_send_onboarding_steps(message, first_name))
