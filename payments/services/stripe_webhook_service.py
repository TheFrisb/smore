import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum

from django.db import models
from django.utils import timezone

from accounts.models import (
    User,
    UserSubscription,
    PurchasedPredictions,
    PurchasedTickets,
    PurchasedDailyOffer,
)
from accounts.services.referral_service import ReferralService
from core.models import Product, Prediction, Ticket
from payments.services.base_stripe_service import BaseStripeService

logger = logging.getLogger(__name__)


class StripeWebhookEvent(Enum):
    INVOICE_PAID = "invoice.paid"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"


class StripeWebhookService(BaseStripeService):

    def process_stripe_event(self, payload, sig_header):
        event = self.stripe_client.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )
        event_type = event["type"]

        logger.info(f"Received Stripe event: {event_type}")

        if event_type == StripeWebhookEvent.INVOICE_PAID.value:
            self.process_invoice_paid(event["data"]["object"])

        if event_type == StripeWebhookEvent.PAYMENT_INTENT_SUCCEEDED.value:
            self.process_payment_intent_succeeded(event["data"]["object"])

        if event_type == StripeWebhookEvent.SUBSCRIPTION_UPDATED.value:
            self.process_subscription_updated(event["data"]["object"])

        if event_type == StripeWebhookEvent.SUBSCRIPTION_DELETED.value:
            self.process_subscription_deleted(event["data"]["object"])

    def process_invoice_paid(self, event_data):
        new_subscription = False
        stripe_customer_id = event_data["customer"]
        stripe_subscription_id = event_data["subscription"]
        amount_paid_cents = event_data.get("amount_paid", 0)
        meta_data = self.get_stripe_subscription_by_id(stripe_subscription_id).get(
            "metadata", {}
        )
        first_chosen_product_id = meta_data.get("first_chosen_product_id", None)
        first_chosen_product = Product.objects.filter(
            id=first_chosen_product_id
        ).first()
        logger.info(
            f"Received invoice paid event for subscription: {stripe_subscription_id} and customer {stripe_customer_id}"
        )

        try:
            user = User.objects.get(stripe_customer_id=stripe_customer_id)
        except User.DoesNotExist:
            logger.error(f"No user found with stripe customer ID: {stripe_customer_id}")
            return

        logger.info(f"Matched invoice paid event to user: {user.username}")

        stripe_subscription = self.get_stripe_subscription_by_id(stripe_subscription_id)
        amount_paid = Decimal(amount_paid_cents / 100)
        stripe_subscription_total_price = self.calculate_subscription_price(
            stripe_subscription
        )

        stripe_subscription_items = stripe_subscription["items"]["data"]
        if not stripe_subscription_items:
            logger.error(
                f"No subscription items found for subscription ID: {stripe_subscription_id}"
            )
            return
        subscription_start_time = datetime.fromtimestamp(
            stripe_subscription.start_date, tz=timezone.get_current_timezone()
        )
        subscription_end_time = datetime.fromtimestamp(
            stripe_subscription.current_period_end, tz=timezone.get_current_timezone()
        )
        internal_subscription_status = (
            UserSubscription.Status.ACTIVE
            if stripe_subscription.status == "active"
            else UserSubscription.Status.INACTIVE
        )

        first_item = stripe_subscription_items[0]
        plan_interval = first_item["plan"]["interval"]
        internal_frequency_status = (
            UserSubscription.Frequency.MONTHLY
            if plan_interval == "month"
            else UserSubscription.Frequency.YEARLY
        )
        stripe_price_ids = [item["price"]["id"] for item in stripe_subscription_items]
        internal_products = Product.objects.filter(
            models.Q(monthly_price_stripe_id__in=stripe_price_ids)
            | models.Q(yearly_price_stripe_id__in=stripe_price_ids)
            | models.Q(discounted_monthly_price_stripe_id__in=stripe_price_ids)
            | models.Q(discounted_yearly_price_stripe_id__in=stripe_price_ids)
        )

        if not internal_products.exists():
            logger.error(
                f"No products for price IDs: {stripe_price_ids} found when processing subscription ID: {stripe_subscription_id}"
            )
            return

        user_subscription = UserSubscription.objects.filter(
            user=user, stripe_subscription_id=stripe_subscription_id
        ).first()

        if not user_subscription:

            existing_subscription = UserSubscription.objects.filter(user=user).first()
            if existing_subscription:
                logger.info(
                    f"Existing subscription found for user {user.username} and subscription ID {existing_subscription.stripe_subscription_id}"
                )
                try:
                    self.deactivate_subscription(
                        existing_subscription.stripe_subscription_id
                    )
                except Exception as e:
                    logger.error(f"Error while deactivating existing subscription: {e}")
                existing_subscription.delete()

            logger.info(
                f"No internal subscription found for user {user.username} and subscription ID {stripe_subscription_id}"
            )
            logger.info("Creating new subscription...")
            user_subscription = UserSubscription.objects.create(
                user=user,
                status=internal_subscription_status,
                frequency=internal_frequency_status,
                price=stripe_subscription_total_price,
                start_date=subscription_start_time,
                end_date=subscription_end_time,
                stripe_subscription_id=stripe_subscription_id,
                first_chosen_product=first_chosen_product,
            )
            new_subscription = True

        else:
            logger.info(
                f"Updating existing subscription for user {user.username} and subscription ID {stripe_subscription_id}"
            )
            user_subscription.status = internal_subscription_status
            user_subscription.start_date = subscription_start_time
            user_subscription.end_date = subscription_end_time
            user_subscription.frequency = internal_frequency_status
            user_subscription.price = stripe_subscription_total_price
            if first_chosen_product:
                user_subscription.first_chosen_product = first_chosen_product
            user_subscription.save()

        user_subscription.products.set(internal_products)

        referral_service = ReferralService()
        referral_service.award_commissions_for_invoice(user, amount_paid)

        if new_subscription:
            self.mailer.send_new_subscription_email(user, user_subscription)

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

    def process_subscription_updated(self, event_data):
        logger.info(f"Received subscription updated event: {event_data}")
        stripe_subscription_id = event_data["id"]
        stripe_customer_id = event_data["customer"]
        subscription_status = event_data["status"]

        logger.info(
            f"Received subscription updated event with status: {subscription_status} for subscription: {stripe_subscription_id} and customer {stripe_customer_id}"
        )

        if subscription_status == "active":
            UserSubscription.objects.filter(
                user__stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
            ).update(status=UserSubscription.Status.ACTIVE)
            return

        if subscription_status not in ["canceled", "past_due", "incomplete_expired"]:
            logger.info(
                f"Subscription with ID: {stripe_subscription_id} is updated to: {subscription_status}"
            )
            return

        logger.info(f"Subscription canceled for subscription: {stripe_subscription_id}")
        self.mark_subscription_inactive(stripe_customer_id, stripe_subscription_id)

    def process_subscription_deleted(self, event_data):
        stripe_subscription_id = event_data["id"]
        stripe_customer_id = event_data["customer"]
        subscription_status = event_data["status"]

        logger.info(
            f"Received subscription deleted event with status: {subscription_status} for subscription: {stripe_subscription_id} and customer {stripe_customer_id}"
        )

        self.mark_subscription_inactive(stripe_customer_id, stripe_subscription_id)

    def mark_subscription_inactive(
        self, stripe_customer_id: str, stripe_subscription_id: str
    ):
        logger.info(
            f"Deleting internal subscription for subscription: {stripe_subscription_id} and customer {stripe_customer_id}"
        )
        UserSubscription.objects.filter(
            user__stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
        ).update(status=UserSubscription.Status.INACTIVE)
