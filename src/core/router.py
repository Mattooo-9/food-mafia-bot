from aiogram import Router
from .handlers import onboarding, catalog, payments

def get_main_router() -> Router:
    main_router = Router()
    main_router.include_router(onboarding.router)
    main_router.include_router(catalog.router)
    main_router.include_router(payments.router)
    return main_router
