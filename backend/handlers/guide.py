"""Интерактивное сопровождение пользователя в чате."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.handlers.start import webapp_keyboard
from backend.utils.categories import categorize_text

router = Router(name="guide")

_GUIDE_KEYWORDS: dict[tuple[str, ...], str] = {
    ("суп", "борщ", "бульон", "щи", "уха"): (
        "🍲 Откройте приложение → напишите «суп» → «Найти». Покажу только супы рядом."
    ),
    ("салат", "закуск"): (
        "🥗 В приложении нажмите «Салат» или напишите запрос — ИИ сам отфильтрует."
    ),
    ("заказ", "хочу", "нужно", "голод", "поесть"): (
        "📋 Готовое — в ленте. Нет подходящего — «Запрос поварам» в заказах."
    ),
    ("повар", "готов", "кухн"): (
        "👨‍🍳 Стать поваром: /become_cook. Заказы и запросы — в «Моей кухне»."
    ),
    ("помощ", "как", "что делать"): (
        "💡 1) Геолокация  2) Напишите что хотите  3) Закажите или запрос поварам"
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
    name = first_name or "друг"
    steps = (
        f"{name}, быстро:\n\n"
        "📍 Геолокация — еда рядом\n"
        "🍲 Напишите «обед» или «суп» — подберу сам\n"
        "📋 Нет готового? Запрос поварам"
    )
    await message.answer(steps, reply_markup=webapp_keyboard())


@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def guide_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        return
    reply = _match_guide(text)
    if not reply:
        cat = categorize_text(query=text)
        if cat.get("score", 0) >= 1 and cat["group"] != "Разное":
            reply = f"Понял: «{cat['label']}». Откройте приложение — поиск уже настроен."
        else:
            return

    await message.answer(reply, reply_markup=webapp_keyboard())


async def schedule_new_user_guide(message: Message, first_name: str | None) -> None:
    asyncio.create_task(_send_onboarding_steps(message, first_name))
