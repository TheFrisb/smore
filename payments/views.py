import logging

import stripe
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Product
from payments.services.stripe_checkout_service import (
    StripeCheckoutService,
    StripePortalSessionFlow,
)
from payments.services.stripe_webhook_service import StripeWebhookService

logger = logging.getLogger(__name__)


# Create your views here.
class CreateCheckoutUrlView(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        products = serializers.ListField(child=serializers.IntegerField())
        frequency = serializers.ChoiceField(choices=["month", "year"])

    class OutputSerializer(serializers.Serializer):
        url = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # if user has subscription get portal session
        if request.user.subscription_is_active:
            return Response({"url": reverse("payments:manage-subscription")})

        products = Product.objects.filter(id__in=serializer.validated_data["products"])

        if not products.exists():
            raise serializers.ValidationError("No products found.")

        if len(products) != len(serializer.validated_data["products"]):
            raise serializers.ValidationError("Some products not found.")

        price_ids = []
        if serializer.validated_data["frequency"] == "month":
            price_ids = [product.monthly_price_stripe_id for product in products]
        elif serializer.validated_data["frequency"] == "year":
            price_ids = [product.yearly_price_stripe_id for product in products]

        checkout_session = self.service.create_checkout_session(request.user, price_ids)

        output_serializer = self.OutputSerializer(data={"url": checkout_session.url})
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)


class ManageSubscriptionView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.subscription_is_active:
            logger.info(
                f"User: {self.request.user.id} attempted to manage subscription without having an active subscription."
            )
            return reverse("core:plans")

        service = StripeCheckoutService()
        portal_session = service.create_portal_session(self.request.user)
        return portal_session.url


class UpdateSubscriptionView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.subscription_is_active:
            logger.info(
                f"User: {self.request.user.id} attempted to update subscription without having an active subscription."
            )
            return reverse("core:plans")

        service = StripeCheckoutService()
        portal_session = service.create_portal_session(
            self.request.user, StripePortalSessionFlow.UPDATE_SUBSCRIPTION
        )
        return portal_session.url


class PaymentSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        messages.success(
            self.request,
            'You are now subscribed. You can manage your plan in the "Manage Plan" section.',
        )
        return reverse("accounts:my_account")


@csrf_exempt
def stripe_webhook(request):
    stripe_service = StripeWebhookService()
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe_service.process_stripe_event(payload, sig_header)
    except ValueError:
        logger.error("Invalid payload")
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse("Invalid signature", status=400)

    return JsonResponse({"status": "success"})
