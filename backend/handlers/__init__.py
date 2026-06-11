from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from backend.handlers.cook import router as cook_router
from backend.handlers.location import router as location_router
from backend.handlers.orders import router as orders_router
from backend.handlers.start import router as start_router


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(location_router)
    dp.include_router(cook_router)
    dp.include_router(orders_router)
    return dp
