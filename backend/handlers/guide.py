"""Интерактивное сопровождение пользователя в чате."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.handlers.start import main_reply_keyboard, webapp_keyboard
from backend.utils.categories import categorize_text

router = Router(name="guide")

_GUIDE_KEYWORDS: dict[tuple[str, ...], str] = {
    ("суп", "борщ", "бульон", "щи", "уха"): (
        "🍲 Ищете суп? Откройте приложение, напишите «суп» и нажмите «Найти» — "
        "покажу только подходящие блюда рядом, без лишнего."
    ),
    ("салат", "закуск"): (
        "🥗 Салаты и закуски — в приложении на вкладке «Лента». "
        "Напишите что хотите, ИИ сам отфильтрует."
    ),
    ("заказ", "хочу", "нужно", "голод"): (
        "📋 Можно заказать готовое блюдо у повара или опубликовать свой запрос — "
        "повара рядом сами возьмут его в работу."
    ),
    ("повар", "готов", "кухн"): (
        "👨‍🍳 Стать поваром: /become_cook или кнопка внизу. "
        "В «Моей кухне» — заказы, запросы покупателей и идеи рецептов."
    ),
    ("помощ", "как", "что делать"): (
        "💡 Коротко:\n"
        "1️⃣ Откройте приложение\n"
        "2️⃣ Разрешите геолокацию\n"
        "3️⃣ Напишите что хотите поесть\n"
        "4️⃣ Закажите или опубликуйте запрос"
    ),
}


def _match_guide(text: str) -> str | None:
    low = text.lower()
    for keys, reply in _GUIDE_KEYWORDS.items():
        if any(k in low for k in keys):
            return reply
    return None


async def _send_onboarding_steps(message: Message, first_name: str | None) -> None:
    await asyncio.sleep(1.5)
    name = first_name or "друг"
    steps = (
        f"{name}, подскажу как начать:\n\n"
        "📍 <b>Шаг 1.</b> Отправьте геолокацию — покажу еду рядом.\n"
        "🍲 <b>Шаг 2.</b> Напишите в приложении, что хотите — подберу по смыслу.\n"
        "📋 <b>Шаг 3.</b> Нет готового? Опубликуйте запрос — повара сами возьмут."
    )
    markup = webapp_keyboard()
    await message.answer(steps, reply_markup=markup)


@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def guide_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        return
    reply = _match_guide(text)
    if not reply:
        cat = categorize_text(query=text)
        if cat.get("score", 0) >= 1 and cat["group"] != "Разное":
            reply = (
                f"Понял: вам ближе «{cat['label']}». "
                "Откройте приложение — там поиск уже настроен под это."
            )
        else:
            return

    markup = webapp_keyboard()
    await message.answer(reply, reply_markup=markup)


async def schedule_new_user_guide(message: Message, first_name: str | None) -> None:
    asyncio.create_task(_send_onboarding_steps(message, first_name))
