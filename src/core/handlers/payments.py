from aiogram import Router, types, F
from ..services.payment_manager import payment_manager

router = Router()

@router.callback_query(F.data.startswith("pay_stars_"))
async def handle_stars_payment(callback: types.CallbackQuery):
    # Process Telegram Stars payment
    await callback.answer("Stars payment initiated...", show_alert=True)

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
