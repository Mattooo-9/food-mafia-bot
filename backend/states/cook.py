from aiogram.fsm.state import State, StatesGroup


class CookRegistration(StatesGroup):
    name = State()
    description = State()
    photo = State()
