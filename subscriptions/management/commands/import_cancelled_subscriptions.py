import logging

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime

from accounts.models import User
from subscriptions.models import BillingProvider, ProductPrice, UserSubscription

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch all cancelled Stripe subscriptions and create corresponding UserSubscriptions"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("Starting to fetch cancelled subscriptions")
        count = 0
        skipped = 0
        for sub in stripe.Subscription.list(status="canceled").auto_paging_iter():
            sub_id = sub["id"]
            logger.info(f"Processing cancelled subscription {sub_id}")
            if UserSubscription.objects.filter(
                provider=BillingProvider.STRIPE, provider_subscription_id=sub_id
            ).exists():
                logger.info(f"Subscription {sub_id} already exists, skipping")
                skipped += 1
                continue
            customer_id = sub["customer"]
            try:
                user = User.objects.get(stripe_customer_id=customer_id)
            except User.DoesNotExist:
                logger.warning(f"No user found for customer {customer_id}, skipping")
                skipped += 1
                continue
            try:
                price_id = sub["items"]["data"][0]["price"]["id"]
                product_price = ProductPrice.objects.get(
                    provider=BillingProvider.STRIPE, provider_price_id=price_id
                )
            except (IndexError, KeyError, ProductPrice.DoesNotExist):
                logger.warning(
                    f"Unable to match product price for sub {sub_id}, skipping"
                )
                skipped += 1
                continue
            if not sub["ended_at"]:
                logger.warning(f"No ended_at for sub {sub_id}, skipping")
                skipped += 1
                continue
            start_date = datetime.fromtimestamp(
                sub["start_date"], tz=timezone.get_default_timezone()
            )
            end_date = datetime.fromtimestamp(
                sub["ended_at"], tz=timezone.get_default_timezone()
            )
            user_sub = UserSubscription.objects.create(
                user=user,
                product_price=product_price,
                provider=BillingProvider.STRIPE,
                provider_subscription_id=sub_id,
                is_active=False,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info(f"Created UserSubscription {user_sub.id} for sub {sub_id}")
            count += 1
        logger.info(f"Finished. Created {count} subscriptions, skipped {skipped}")
