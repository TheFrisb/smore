import stripe
from django.core.management import BaseCommand, CommandError

from accounts.models import User
from payments.services.stripe.stripe_subscription_service import (
    StripeSubscriptionService,
)


class Command(BaseCommand):
    help = "Split multi-product Stripe subscriptions into per-product subscriptions, while preserving billing periods."

    def __init__(self):
        super().__init__()
        self.service = StripeSubscriptionService()

    def add_arguments(self, parser):
        parser.add_argument(
            "subscription_id",
            type=str,
            help="The Stripe subscription ID you want to split",
        )
        parser.add_argument(
            "--coupon_id",
            type=str,
            help="The Stripe coupon ID to apply to the new (item2) subscription",
            default=None,
        )

    def handle(self, *args, **options):
        subscription_id = options["subscription_id"]
        coupon_id = options["coupon_id"]
        user, original_sub = self._retrieve_user_and_subscription(subscription_id)

        if len(original_sub.items.data) != 2:
            raise CommandError(
                "This command only supports subscriptions with exactly 2 items."
            )

        period_end = original_sub.current_period_end

        item1 = original_sub["items"]["data"][0]
        item2 = original_sub["items"]["data"][1]

        item2_id = item2["id"]
        price_id2 = item2["price"]["id"]
        quantity2 = item2.quantity or 1  # Handle if None/default

        try:
            self.service.stripe_client.SubscriptionItem.delete(
                item2_id, proration_behavior="none"
            )
        except stripe.error.StripeError as e:
            raise CommandError(
                f"Failed to delete item from original subscription: {str(e)}"
            )

        create_params = {
            "customer": user.stripe_customer_id,
            "items": [
                {
                    "price": price_id2,
                    "quantity": quantity2,
                }
            ],
            "trial_end": period_end,
            "proration_behavior": "none",
        }

        if coupon_id:
            create_params["coupon"] = coupon_id

        try:
            new_sub = self.service.stripe_client.Subscription.create(**create_params)
        except stripe.error.StripeError as e:
            raise CommandError(f"Failed to create new subscription: {str(e)}")

        if new_sub.status != "trialing" or (coupon_id and not new_sub.discount):
            raise CommandError(
                "New subscription created but status or discount is unexpected—check Stripe dashboard."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully split subscription {subscription_id}. New sub ID: {new_sub.id}"
            )
        )

    def _retrieve_user_and_subscription(self, subscription_id: str):
        subscription = self.service.get_stripe_subscription_by_id(subscription_id)
        user = User.objects.get(stripe_customer_id=subscription.customer)

        return user, subscription
