import logging

import stripe
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from facebook.services.facebook_pixel import FacebookPixel
from payments.services.stripe.stripe_checkout_service import StripeCheckoutService
from subscriptions.models import (
    BillingProvider,
    PriceCoupon,
    ProductPrice,
    UserSubscription,
)

logger = logging.getLogger(__name__)


class CreateSubscriptionCheckoutUrl(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        product_price = serializers.PrimaryKeyRelatedField(
            queryset=ProductPrice.objects.filter(provider=BillingProvider.STRIPE)
        )

    class OutputSerializer(serializers.Serializer):
        url = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_price = serializer.validated_data["product_price"]
        checkout_session = self.service.create_subscription_checkout_session(
            user=request.user,
            price_id=product_price.provider_price_id,
            coupon=self._get_coupon_if_needed(),
        )

        self._send_fb_event(product_price.product, checkout_session.amount_total)

        output_serializer = self.OutputSerializer({"url": checkout_session.url})
        return Response(output_serializer.data)

    def _get_coupon_if_needed(self):
        user_subscriptions = UserSubscription.objects.filter(
            user=self.request.user, provider=BillingProvider.STRIPE, is_active=True
        )

        if user_subscriptions.count() >= 1:
            return PriceCoupon.objects.filter(
                provider=BillingProvider.STRIPE, is_active=True
            ).first()
        else:
            return None

    def _send_fb_event(self, product, amount_total):
        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.initiate_checkout(product, amount_total)
        except Exception as e:
            logger.error(
                f"Error while sending InitiateCheckout Facebook Pixel event: {e}"
            )


class UpdateSubscriptionView(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        old_product_price = serializers.PrimaryKeyRelatedField(
            queryset=ProductPrice.objects.filter(provider=BillingProvider.STRIPE)
        )

        new_product_price = serializers.PrimaryKeyRelatedField(
            queryset=ProductPrice.objects.filter(provider=BillingProvider.STRIPE)
        )

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_subscription = UserSubscription.objects.filter(
            product_price=serializer.validated_data["old_product_price"]
        ).first()
        if not user_subscription:
            return Response(status=404, data={"message": "User subscription not found"})

        if not user_subscription.is_active:
            return Response(
                status=422, data={"message": "User subscription is not active"}
            )

        stripe_subscription = self.service.get_stripe_subscription_by_id(
            user_subscription.provider_subscription_id
        )
        subscription_item = stripe_subscription["items"]["data"][0]
        if (
            subscription_item.price.id
            != serializer.validated_data["old_product_price"].provider_price_id
        ):
            logger.info(subscription_item.price)

            return Response(
                status=500,
                data={
                    "message": "An unknown error has occurred. Please contact support for assistance"
                },
            )

        items_to_update = {
            "id": subscription_item.id,
            "price": serializer.validated_data["new_product_price"].provider_price_id,
        }

        try:
            self.service.modify_stripe_subscription(
                user_subscription.provider_subscription_id, [items_to_update]
            )
        except stripe.error.CardError as e:
            logger.error(f"Card error while updating subscription: {e}")
            return Response(
                status=400,
                data={
                    "message": e.user_message
                    or "Your card was declined. Please update your payment method"
                },
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error while updating subscription: {e}")
            return Response(
                status=500,
                data={
                    "message": "An error occurred while processing your payment. Please try again later"
                },
            )
        return Response({"message": "Subscription updated successfully."})
