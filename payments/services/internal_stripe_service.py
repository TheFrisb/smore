import logging
from enum import Enum

import stripe
from django.conf import settings
from django.db.models import F

from accounts.models import UserBalance, User, UserSubscription
from core.models import Product

logger = logging.getLogger(__name__)


class StripeWebhookEvent(Enum):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    CHECKOUT_SESSION_EXPIRED = "checkout.session.expired"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"  #
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"  # Subscription cancelled
    INVOICE_PAID = "invoice.paid"  # Provision access


class InternalStripeService:
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET_KEY

    def create_stripe_customer(self, user):
        stripe.api_key = self.api_key
        customer = stripe.Customer.create(email=user.email)
        user.stripe_customer_id = customer["id"]
        user.save()

    def process_stripe_event(self, payload, sig_header):
        event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        event_type = event["type"]

        logger.info(f"Processing Stripe event: {event_type}")

        if event_type != StripeWebhookEvent.CHECKOUT_SESSION_COMPLETED.value:
            logger.info("Not implemented")
            return

        self.process_checkout_session_completed(event["data"]["object"])

    def process_checkout_session_completed(self, event_data):
        user_id = int(event_data["metadata"]["user_id"])
        frequency = event_data["metadata"]["frequency"]
        products = event_data["metadata"]["products"]
        total_price = event_data["metadata"]["total_price"]

        subscription = event_data["subscription"]

        products = Product.objects.filter(id__in=products)

        user = User.objects.get(id=user_id)

        logger.info(f"Processing checkout session completed for user: {user_id}, subscription: {subscription}")
        user_subscription = UserSubscription(
            user=user,
            status=UserSubscription.Status.ACTIVE,
            frequency=frequency,
            price=total_price,
            start_date=event_data["created"],
        )
