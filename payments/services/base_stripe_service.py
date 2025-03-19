import logging
from decimal import Decimal

import stripe
from stripe import Customer, Subscription

from accounts.models import User
from backend import settings
from core.mailer.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class BaseStripeService:
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET_KEY
        self.stripe_client = stripe
        self.stripe_client.api_key = self.api_key
        self.mailer = MailjetService()

    def create_stripe_customer(self, user: User) -> Customer:
        if user.stripe_customer_id:
            raise ValueError(f"User {user.id} already has a Stripe customer ID.")

        customer = self.stripe_client.Customer.create(
            email=user.email, name=user.username, metadata={"user_id": user.id}
        )
        logger.info(f"Created Stripe customer {customer['id']} for user {user.id}")

        user.stripe_customer_id = customer["id"]
        user.save()
        logger.info(
            f"Saved user: {user.id} with Stripe customer ID: {user.stripe_customer_id}"
        )

        return customer

    def get_stripe_subscription_by_id(self, subscription_id: str):
        logger.info(f"Fetching Stripe subscription with ID: {subscription_id}")
        subscription = self.stripe_client.Subscription.retrieve(subscription_id)
        logger.info(f"Successfully fetched subscription with ID: {subscription_id}")

        return subscription

    def calculate_subscription_price(self, subscription: Subscription) -> Decimal:
        total = sum(
            item.price.unit_amount * item.quantity
            for item in subscription["items"]["data"]
        )
        return Decimal(total / 100)

    def modify_stripe_subscription(self, subscription_id: str, items_list: list[dict]):
        logger.info(f"Modifying subscription with ID: {subscription_id}")
        subscription = self.stripe_client.Subscription.retrieve(subscription_id)
        subscription.items = items_list
        subscription.payment_behavior = "pending_if_incomplete"
        subscription.proration_behavior = "always_invoice"

        subscription.save()
        logger.info(f"Successfully modified subscription with ID: {subscription_id}")

    def deactivate_subscription(self, subscription_id: str):
        logger.info(f"Deactivating subscription with ID: {subscription_id}")
        subscription = self.stripe_client.Subscription.retrieve(subscription_id)
        subscription.delete()
        logger.info(f"Successfully deactivated subscription with ID: {subscription_id}")
