import logging
from enum import Enum

import stripe
from django.conf import settings
from django.db.models import F

from accounts.models import UserBalance, User

log = logging.getLogger(__name__)


class StripeWebhookEvent(Enum):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    CHECKOUT_SESSION_EXPIRED = "checkout.session.expired"


class InternalStripeService:
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET_KEY

    def process_stripe_event(self, payload, sig_header):
        event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        event_type = event["type"]

        if event_type != StripeWebhookEvent.CHECKOUT_SESSION_COMPLETED.value:
            log.info("Not implemented")
            return

        self.process_checkout_session_completed(event["data"]["object"])

    def process_checkout_session_completed(self, event_data):
        user_id = int(event_data["metadata"]["user_id"])

        user = User.objects.get(id=user_id)
        total_amount = int(event_data["amount_total"]) / 100

        five_percent = total_amount * 0.05
        twenty_percent = total_amount * 0.20

        if hasattr(user, "referral") and user.referral.referrer:

            UserBalance.objects.filter(user=user.referral.referrer).update(
                balance=F("balance") + twenty_percent
            )

            # Check if the direct referrer has their own referrer
            direct_referrer = user.referral.referrer
            if (
                    hasattr(direct_referrer, "referral")
                    and direct_referrer.referral.referrer
            ):
                UserBalance.objects.filter(
                    user=direct_referrer.referral.referrer
                ).update(balance=F("balance") + five_percent)
