class PaymentManager:
    @staticmethod
    def get_payment_method(color_category: str):
        """
        Determines the payment method based on the Rainbow category.
        Red/Orange (Energy) might support quick Telegram Stars.
        Green/Purple (Detox/Balance) might require TON Escrow for higher trust.
        """
        if color_category in ["Red", "Orange"]:
            return ["STARS", "TON"]
        return ["TON"]

    @staticmethod
    async def create_stars_invoice(item_name: str, price: int):
        # Logic to generate Telegram Stars invoice
        pass

payment_manager = PaymentManager()
