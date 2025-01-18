import logging
from enum import Enum
from typing import List

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.urls import reverse
from stripe.checkout import Session

from accounts.models import User
from payments.services.base_stripe_service import BaseStripeService

logger = logging.getLogger(__name__)


class StripePortalSessionFlow(Enum):
    UPDATE_SUBSCRIPTION = "update_subscription"
    MANAGE_SUBSCRIPTION = "manage_subscription"


class StripeCheckoutService(BaseStripeService):

    def create_checkout_session(
            self, user: User | AbstractBaseUser, price_ids: List[str]
    ) -> Session:
        checkout_session = self.stripe_client.checkout.Session.create(
            success_url=f"{settings.BASE_URL}{reverse('payments:payment_success')}",
            cancel_url=f"{settings.BASE_URL}{reverse('core:plans')}",
            mode="subscription",
            customer=user.stripe_customer_id,
            line_items=self.get_line_items(price_ids),
        )

        logger.info(
            f"Created checkout session for user: {user.id} with session ID: {checkout_session.id}"
        )

        return checkout_session

    def get_line_items(self, price_ids: List[str]) -> List[dict]:
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
