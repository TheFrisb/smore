import logging
from enum import Enum

from accounts.models import (
    User,
    PurchasedPredictions,
    PurchasedTickets,
    PurchasedDailyOffer,
)
from core.models import Prediction, Ticket
from payments.services.base_stripe_service import BaseStripeService
from payments.services.stripe_subscription_service import StripeSubscriptionService
from subscriptions.models import UserSubscription

logger = logging.getLogger(__name__)


class StripeWebhookEvent(Enum):
    INVOICE_PAID = "invoice.paid"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"


class StripeWebhookService(BaseStripeService):
    def __init__(self):
        super().__init__()
        self.subscription_service = StripeSubscriptionService()

    def process_stripe_event(self, payload, sig_header):
        event = self.stripe_client.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )
        event_type = event["type"]

        logger.info(f"Received Stripe event: {event_type}")

        if event_type == StripeWebhookEvent.INVOICE_PAID.value:
            self.process_invoice_paid(event["data"]["object"])

        if event_type == StripeWebhookEvent.SUBSCRIPTION_UPDATED.value:
            self.process_subscription_updated(event["data"]["object"])

        if event_type == StripeWebhookEvent.SUBSCRIPTION_DELETED.value:
            self.process_subscription_deleted(event["data"]["object"])

        if event_type == StripeWebhookEvent.PAYMENT_INTENT_SUCCEEDED.value:
            self.process_payment_intent_succeeded(event["data"]["object"])

    def process_invoice_paid(self, event_data):
        stripe_subscription_id = event_data["subscription"]
        stripe_subscription = self.get_stripe_subscription_by_id(stripe_subscription_id)

        logger.info(
            f"Received invoice paid event for stripe subscription ID: {stripe_subscription_id}"
        )

        if UserSubscription.objects.filter(
            provider_subscription_id=stripe_subscription_id
        ).exists():
            logger.info(
                f"The invoice paid event for stripe subscription ID: {stripe_subscription_id} is for an existing subscription, updating it"
            )
            self.subscription_service.update_subscription(stripe_subscription)
        else:
            logger.info(
                f"The invoice paid event for stripe subscription ID: {stripe_subscription_id} is for a new subscription, creating it"
            )

            self.subscription_service.create_user_subscription(stripe_subscription)

    def process_subscription_updated(self, event_data):
        logger.info(f"Received subscription updated event: {event_data}")
        stripe_subscription_id = event_data["id"]
        stripe_customer_id = event_data["customer"]
        subscription_status = event_data["status"]

        logger.info(
            f"Received subscription updated event with status: {subscription_status} for subscription: {stripe_subscription_id} and customer {stripe_customer_id}"
        )

    def process_subscription_deleted(self, event_data):
        stripe_subscription_id = event_data["id"]
        stripe_subscription = self.get_stripe_subscription_by_id(stripe_subscription_id)

        self.subscription_service.deactivate_user_subscription(stripe_subscription)

    def process_payment_intent_succeeded(self, event_data):
        logger.info(f"Received payment intent ({event_data['id']}) succeeded event")
        stripe_customer_id = event_data["customer"]
        purchased_object_id = event_data["metadata"].get("purchased_object_id", None)
        purchased_object_type = event_data["metadata"].get(
            "purchased_object_type", None
        )

        if not purchased_object_id:
            logger.info(
                f"No purchased object id found in payment intent: {event_data['id']}"
            )
            return

        if not purchased_object_type:
            logger.info(
                f"No purchased object type found in payment intent: {event_data['id']}"
            )
            return

        customer = User.objects.filter(stripe_customer_id=stripe_customer_id).first()
        if not customer:
            logger.error(f"No customer found with stripe ID: {stripe_customer_id}")
            return

        obj = None
        if purchased_object_type == "prediction":
            logger.info(
                f"Purchased object is a prediction with ID: {purchased_object_id} for customer: {customer.username}"
            )
            try:
                obj = Prediction.objects.get(id=purchased_object_id)
                purchased_prediction = PurchasedPredictions.objects.create(
                    user=customer,
                    prediction=obj,
                )
                logger.info(
                    f"Created purchased prediction: {purchased_prediction.id} for user: {customer.username}."
                )
                return
            except Prediction.DoesNotExist:
                logger.error(
                    f"No prediction found with ID: {purchased_object_id} for customer: {customer.username}"
                )
                return
        elif purchased_object_type == "ticket":
            logger.info(
                f"Purchased object is a ticket with ID: {purchased_object_id} for customer: {customer.username}"
            )
            try:
                obj = Ticket.objects.get(id=purchased_object_id)
                purchased_ticket = PurchasedTickets.objects.create(
                    user=customer,
                    ticket=obj,
                )
                logger.info(
                    f"Created purchased ticket: {purchased_ticket.id} for user: {customer.username}."
                )
                return
            except Ticket.DoesNotExist:
                logger.error(
                    f"No ticket found with ID: {purchased_object_id} for customer: {customer.username}"
                )
                return
        elif purchased_object_type == "daily_offer":
            logger.info(
                f"Purchased object is a daily_offer with ID: {purchased_object_id} for customer: {customer.username}"
            )

            try:
                obj = PurchasedDailyOffer.objects.get(
                    id=purchased_object_id, user=customer
                )
                obj.status = PurchasedDailyOffer.Status.PURCHASED
                obj.save()

                logger.info(
                    f"Created purchased daily offer with id: {purchased_object_id} for user: {customer.username}."
                )
                return
            except PurchasedDailyOffer.DoesNotExist:
                logger.error(
                    f"No daily offer with ID: {purchased_object_id} for customer: {customer.username} was found."
                )
                return

        logger.error(
            f"Purchased object type {purchased_object_type} (ID: {purchased_object_id}) not recognized for customer: {customer.username}"
        )
