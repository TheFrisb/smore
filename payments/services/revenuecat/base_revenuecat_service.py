import logging
from datetime import datetime, timezone

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware

from accounts.models import User
from subscriptions.models import BillingProvider, ProductPrice, UserSubscription

logger = logging.getLogger(__name__)


class BaseRevenuecatService:
    def __init__(self):
        self.api_key = settings.REVENUECAT_API_KEY

    def expire_subscription(self, app_user_id, external_product_id: str):
        subscription = UserSubscription.objects.filter(
            provider=BillingProvider.REVENUECAT,
            provider_subscription_id=self.construct_external_id(
                app_user_id, external_product_id
            ),
        ).first()

        if not subscription:
            logger.warning(
                f"Could not expire subscription for app_user_id: {app_user_id} and external_product_id: {external_product_id}"
            )
            return None

        subscription.is_active = False
        subscription.save()

        return subscription

    def process_subscription_data(
        self, external_product_id: str, subscription_data: dict
    ):
        transaction_id = subscription_data["transaction_id"]
        logger.info(
            f"Processing revenuecat subscription for transaction ID: {transaction_id}"
        )

        user = self.get_user(subscription_data)
        product_price = self.get_product_price(external_product_id)
        start_date, end_date = self._get_start_and_end_datetimes(subscription_data)

        if not user or not product_price:
            logger.error(
                f"Either no user: {user} or product_price was matched: {product_price}. Returning"
            )
            return

        existing_subscription = UserSubscription.objects.filter(
            user=user,
            product_price=product_price,
            is_active=True,
            provider=BillingProvider.REVENUECAT,
        ).first()

        if existing_subscription:
            logger.info(
                f"Matched transaction ID: {transaction_id} to user subscription ID: {existing_subscription.id}"
            )
            existing_subscription.end_date = end_date
            existing_subscription.is_active = True
            existing_subscription.save()
        else:
            logger.info(
                f"Creating new user subscription for transaction ID: {transaction_id}"
            )
            UserSubscription.objects.create(
                user=user,
                product_price=product_price,
                provider=BillingProvider.REVENUECAT,
                start_date=start_date,
                end_date=end_date,
                provider_subscription_id=self.construct_external_id(
                    user.id, product_price.provider_price_id
                ),
            )

        return

    def get_user(self, subscription_data):
        app_user_id = subscription_data["app_user_id"]

        user = User.objects.filter(id=int(app_user_id)).first()

        if not user:
            logger.warning(f"No user found for revenue cat app user ID: {app_user_id}")
            return None

        logger.info(
            f"Matched revenuecat app user ID: {app_user_id} to user ID: {user.id}"
        )
        return user

    def get_product_price(self, external_product_id):
        product_price = ProductPrice.objects.filter(
            provider=BillingProvider.REVENUECAT, provider_price_id=external_product_id
        ).first()

        if not product_price:
            logger.warning(
                f"No product price found for revenuecat product: {external_product_id}"
            )
            return None

        logger.info(
            f"Matched revenuecat product ID: {external_product_id} to product price ID: {product_price.id}"
        )
        return product_price

    def _get_start_and_end_datetimes(self, subscription_data: dict):
        created_at = parse_datetime(subscription_data["purchase_date"])
        expires_at = parse_datetime(subscription_data["expires_date"])

        if is_naive(created_at):
            created_at = make_aware(created_at)

        if is_naive(expires_at):
            expires_at = make_aware(expires_at)

        return created_at, expires_at

    def get_start_and_end_datetimes_from_ms(self, subscription_data: dict):
        purchased_at_ms = subscription_data["purchased_at_ms"]
        expiration_at_ms = subscription_data["expiration_at_ms"]

        purchased_at = datetime.fromtimestamp(purchased_at_ms / 1000, tz=timezone.utc)
        expiration_at = datetime.fromtimestamp(expiration_at_ms / 1000, tz=timezone.utc)

        return purchased_at, expiration_at

    def construct_external_id(self, user_id, price_id):
        return f"{user_id}-{price_id}"
