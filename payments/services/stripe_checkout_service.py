import logging
from enum import Enum
from typing import List

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.urls import reverse
from django.utils import timezone
from stripe.checkout import Session

from accounts.models import User
from core.models import Prediction, Ticket
from payments.services.base_stripe_service import BaseStripeService

logger = logging.getLogger(__name__)


class StripePortalSessionFlow(Enum):
    UPDATE_SUBSCRIPTION = "update_subscription"
    MANAGE_SUBSCRIPTION = "manage_subscription"


class StripeCheckoutService(BaseStripeService):

    def create_subscription_checkout_session(
        self,
        user: User | AbstractBaseUser,
        price_ids: List[str],
        first_chosen_product_id: int,
    ) -> Session:
        metadata = (
            {
                "first_chosen_product_id": first_chosen_product_id,
            }
            if first_chosen_product_id
            else None
        )
        logger.info(
            f"Metadata: {metadata} for user: {user.id} with first chosen product ID: {first_chosen_product_id}"
        )

        checkout_session = self.stripe_client.checkout.Session.create(
            success_url=f"{settings.BASE_URL}{reverse('payments:payment_success')}",
            cancel_url=f"{settings.BASE_URL}{reverse('core:plans')}",
            mode="subscription",
            customer=user.stripe_customer_id,
            line_items=self.get_subscription_line_items(price_ids),
            consent_collection={"terms_of_service": "required"},
            subscription_data={"metadata": metadata} if metadata else None,
        )

        logger.info(
            f"Created checkout session for user: {user.id} with session ID: {checkout_session.id}"
        )

        return checkout_session

    def create_onetime_prediction_checkout_session(
        self, user: User | AbstractBaseUser, prediction: Prediction
    ) -> Session:
        checkout_session = self.stripe_client.checkout.Session.create(
            success_url=f"{settings.BASE_URL}{reverse('payments:purchase_payment_success', kwargs={'prediction_pk': prediction.id})}",
            cancel_url=f"{settings.BASE_URL}{reverse('core:detailed_prediction', kwargs={'pk': prediction.id})}",
            mode="payment",
            customer=user.stripe_customer_id,
            line_items=self.get_onetime_prediction_line_items(prediction),
            payment_intent_data={
                "metadata": {
                    "purchased_object_id": prediction.id,
                    "purchased_object_type": "prediction",
                }
            },
            payment_method_types=["card"],
            consent_collection={"terms_of_service": "required"},
        )

        logger.info(
            f"Created one-time prediction checkout session for user: {user.id} with session ID: {checkout_session.id}"
        )

        return checkout_session

    def create_onetime_ticket_checkout_session(
        self, user: User | AbstractBaseUser, ticket: Ticket
    ) -> Session:
        checkout_session = self.stripe_client.checkout.Session.create(
            success_url=f"{settings.BASE_URL}{reverse('core:upcoming_matches')}",
            cancel_url=f"{settings.BASE_URL}{reverse('core:upcoming_matches')}",
            mode="payment",
            customer=user.stripe_customer_id,
            line_items=self.get_onetime_ticket_line_items(ticket),
            payment_intent_data={
                "metadata": {
                    "purchased_object_id": ticket.id,
                    "purchased_object_type": "ticket",
                }
            },
            payment_method_types=["card"],
            consent_collection={"terms_of_service": "required"},
        )

        logger.info(
            f"Created one-time ticket checkout session for user: {user.id} with session ID: {checkout_session.id}"
        )

        return checkout_session

    def get_subscription_line_items(self, price_ids: List[str]) -> List[dict]:
        return [{"price": price_id, "quantity": 1} for price_id in price_ids]

    def create_portal_session(
        self,
        user: User | AbstractBaseUser,
        portal_flow: StripePortalSessionFlow = StripePortalSessionFlow.MANAGE_SUBSCRIPTION,
    ) -> Session:
        flow = None

        if portal_flow == StripePortalSessionFlow.UPDATE_SUBSCRIPTION:
            flow = {
                "type": "subscription_update",
                "subscription_update": {
                    "subscription": user.subscription.stripe_subscription_id,
                },
            }

        portal_session = self.stripe_client.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{settings.BASE_URL}{reverse('accounts:manage_plan')}",
            flow_data=flow,
        )

        logger.info(
            f"Created portal session for user: {user.id} with session ID: {portal_session.id}"
        )

        return portal_session

    def get_onetime_prediction_line_items(self, prediction):
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Premium prediction: {prediction.match.home_team.name} vs {prediction.match.away_team.name}",
                    },
                    "unit_amount": 999,
                },
                "quantity": 1,
            }
        ]

    def get_onetime_ticket_line_items(self, ticket: Ticket):
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{ticket.product.get_name_display()} ticket",
                    },
                    "unit_amount": 999,
                },
                "quantity": 1,
            }
        ]

    def get_onetime_daily_offer_item(self):
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Unlock Smore's predictions for: {timezone.now().strftime('%m/%d/%Y')}"
                    "unit_amount": 2499,
                },
                "quantity": 1,
            }
        ]

    def update_subscription_items(
        self, user: User, new_price_ids: List[str]
    ) -> Session:
        subscription_id = user.subscription.stripe_subscription_id
        subscription = self.stripe_client.Subscription.retrieve(subscription_id)
        items = [{"price": price_id} for price_id in new_price_ids]
        subscription.items = items
        subscription.save()
        return subscription

    def create_onetime_daily_offer_checkout_session(self, user, daily_offer):
        checkout_session = self.stripe_client.checkout.Session.create(
            success_url=f"{settings.BASE_URL}{reverse('core:upcoming_matches')}",
            cancel_url=f"{settings.BASE_URL}{reverse('core:upcoming_matches')}",
            mode="payment",
            customer=user.stripe_customer_id,
            line_items=self.get_onetime_daily_offer_item(),
            payment_intent_data={
                "metadata": {
                    "purchased_object_id": daily_offer.id,
                    "purchased_object_type": "daily_offer",
                }
            },
            payment_method_types=["card"],
            consent_collection={"terms_of_service": "required"},
        )

        logger.info(
            f"Created one-time daily offer checkout session for user: {user.id} with session ID: {checkout_session.id}"
        )

        return checkout_session
