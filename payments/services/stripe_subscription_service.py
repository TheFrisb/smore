import logging
from datetime import datetime

from django.utils import timezone
from stripe import Subscription

from accounts.models import User
from accounts.services.referral_service import ReferralService
from payments.services.base_stripe_service import BaseStripeService
from subscriptions.models import UserSubscription, BillingProvider, ProductPrice

logger = logging.getLogger(__name__)


class StripeSubscriptionService(BaseStripeService):
    def __init__(self):
        super().__init__()
        self.referral_service = ReferralService()

    def create_user_subscription(
        self, stripe_subscription: Subscription
    ) -> UserSubscription:
        logger.info(stripe_subscription)
        logger.info(f"Stripe customer: {stripe_subscription.customer}")
        logger.info(
            f"Creating new stripe subscription for subscription ID: {stripe_subscription.id} and stripe customer ID: {stripe_subscription.customer}"
        )

        stripe_customer_id = stripe_subscription.customer

        user = User.objects.get(stripe_customer_id=stripe_customer_id)
        product_price = self._get_product_price(stripe_subscription)

        start_datetime, end_datetime = self._get_subscription_start_and_end_datetimes(
            stripe_subscription
        )

        user_subscription = UserSubscription.objects.create(
            user=user,
            product_price=product_price,
            provider=BillingProvider.STRIPE,
            provider_subscription_id=stripe_subscription.id,
            is_active=True,
            start_date=start_datetime,
            end_date=end_datetime,
        )

        return user_subscription

    def update_subscription(
        self, stripe_subscription: Subscription
    ) -> UserSubscription:
        logger.info(
            f"Updating stripe subscription with ID: {stripe_subscription.id} and stripe customer ID: {stripe_subscription.customer}"
        )

        user_subscription = UserSubscription.objects.get(
            provider=BillingProvider.STRIPE,
            provider_subscription_id=stripe_subscription.id,
        )

        product_price = self._get_product_price(stripe_subscription)
        start_datetime, end_datetime = self._get_subscription_start_and_end_datetimes(
            stripe_subscription
        )

        user_subscription.product_price = product_price
        user_subscription.start_date = start_datetime
        user_subscription.end_date = end_datetime

        user_subscription.save()

        return user_subscription

    def deactivate_user_subscription(self, stripe_subscription: Subscription):
        logger.info(f"Deactivating subscription: {stripe_subscription.id}")

        user_subscription = UserSubscription.objects.filter(
            provider=BillingProvider.STRIPE,
            provider_subscription_id=stripe_subscription.id,
        ).first()

        if not user_subscription:
            logger.warning(
                f"No active subscription found for Stripe subscription ID: {stripe_subscription.id}. Nothing to deactivate"
            )
            return

        user_subscription.is_active = False
        user_subscription.save()

        logger.info(
            f"Deactivated subscription: {stripe_subscription.id} for user: {user_subscription.user.id}"
        )

    @staticmethod
    def _get_subscription_start_and_end_datetimes(stripe_subscription: Subscription):
        stripe_price_data = stripe_subscription["items"]["data"][0]
        next_due_date: int = stripe_price_data["current_period_end"]

        subscription_start_time = datetime.fromtimestamp(
            stripe_subscription.start_date, tz=timezone.get_default_timezone()
        )
        subscription_end_time = datetime.fromtimestamp(
            next_due_date, tz=timezone.get_default_timezone()
        )

        return subscription_start_time, subscription_end_time

    @staticmethod
    def _get_product_price(stripe_subscription) -> ProductPrice:
        product_price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
        return ProductPrice.objects.get(
            provider=BillingProvider.STRIPE, provider_price_id=product_price_id
        )
