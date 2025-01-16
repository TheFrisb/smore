import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from stripe import StripeError

from core.models import Product
from payments.services.internal_stripe_service import InternalStripeService

logger = logging.getLogger(__name__)


# Create your views here.
class CreateCheckoutUrlView(APIView):
    def __init__(self):
        super().__init__()
        self.stripe_secret_key = settings.STRIPE_SECRET_KEY

    class InputSerializer(serializers.Serializer):
        products = serializers.ListField(child=serializers.IntegerField())
        frequency = serializers.ChoiceField(choices=["month", "year"])

    class OutputSerializer(serializers.Serializer):
        checkout_url = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        products = Product.objects.filter(id__in=serializer.validated_data["products"])

        if not products.exists():
            raise serializers.ValidationError("No products found.")

        if len(products) != len(serializer.validated_data["products"]):
            raise serializers.ValidationError("Some products not found.")

        try:
            checkout_session = self.create_stripe_checkout_session(
                products, request.user, serializer.validated_data["frequency"]
            )
        except StripeError as e:
            raise serializers.ValidationError(f"Stripe error: {e.error.message}")

        output_serializer = self.OutputSerializer(
            data={"checkout_url": checkout_session.url}
        )
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)

    def calculate_total_price(self, products, frequency):
        total_price = 0
        for product in products:
            if frequency == "month":
                total_price += product.monthly_price
            else:
                total_price += product.annual_price

        return total_price

    def create_stripe_checkout_session(self, products, user, frequency):
        # Create a line item for each product
        line_items = []
        i = 1
        for product in products:
            if frequency == "month":
                price = product.monthly_price
            else:
                price = product.annual_price
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": product.name,
                        },
                        "unit_amount": int(price * 100),
                        "recurring": {
                            "interval": frequency,
                        },
                    },
                    "quantity": 1,
                }
            )

            i += 1

        session = stripe.checkout.Session.create(
            api_key=self.stripe_secret_key,
            payment_method_types=["card"],
            mode="subscription",
            line_items=line_items,
            success_url="https://www.smore.bet/plans/",
            cancel_url="https://www.smore.bet/plans/",
            metadata={
                "user_id": user.id,
                "frequency": frequency,
                "products": products,
                "total_price": self.calculate_total_price(products, frequency),
            },
            customer=user.stripe_customer_id,
        )

        return session


@csrf_exempt
def stripe_webhook(request):
    stripe_service = InternalStripeService()
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
