from accounts.models import UserSubscription
from core.models import Product
from payments.services.base_stripe_service import BaseStripeService


class StripePriceService(BaseStripeService):
    def create_price(
        self,
        product: Product,
        amount: int,
        currency: str,
        interval: UserSubscription.Frequency,
        nickname: str = None,
    ):
        interval_count = (
            3 if interval == UserSubscription.Frequency.THREE_MONTHLY else 1
        )
        computed_interval = (
            "week" if interval == UserSubscription.Frequency.WEEKLY else "month"
        )

        price = self.stripe_client.Price.create(
            product=product.stripe_product_id,
            currency=currency,
            unit_amount=amount,
            recurring={
                "interval": computed_interval,
                "interval_count": interval_count,
            },
            nickname=nickname,
        )

        return price
