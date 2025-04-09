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

from accounts.models import UserSubscription
from core.models import Product, Prediction
from facebook.services.facebook_pixel import FacebookPixel
from payments.services.stripe_checkout_service import (
    StripeCheckoutService,
)
from payments.services.stripe_webhook_service import StripeWebhookService

logger = logging.getLogger(__name__)


# Create your views here.
class CreateSubscriptionCheckoutUrl(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        products = serializers.ListField(child=serializers.IntegerField())
        frequency = serializers.ChoiceField(choices=UserSubscription.Frequency)
        firstProduct = serializers.IntegerField(allow_null=True)

    class OutputSerializer(serializers.Serializer):
        url = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        products = Product.objects.filter(id__in=serializer.validated_data["products"])
        first_chosen_product = Product.objects.filter(
            id=serializer.validated_data["firstProduct"]
        ).first()

        logger.info(f"First chosen product: {first_chosen_product}")

        if not products.exists():
            raise serializers.ValidationError("No products found.")

        if len(products) != len(serializer.validated_data["products"]):
            raise serializers.ValidationError("Some products not found.")

        if (
                serializer.validated_data["firstProduct"]
                not in serializer.validated_data["products"]
        ):
            raise serializers.ValidationError("Invalid 'firstProduct' field.")

        price_ids = self.get_price_ids(
            products, serializer.validated_data["frequency"], first_chosen_product
        )

        checkout_session = self.service.create_subscription_checkout_session(
            request.user,
            price_ids,
            first_chosen_product_id=(
                first_chosen_product.id if first_chosen_product else None
            ),
        )

        try:
            fb_pixel = FacebookPixel(request)
            fb_pixel.initiate_checkout(products.first(), checkout_session.amount_total)
        except Exception as e:
            logger.error(
                f"Error while sending InitiateCheckout Facebook Pixel event: {e}"
            )

        output_serializer = self.OutputSerializer(data={"url": checkout_session.url})
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)

    def use_discounted_prices(self, products):
        """
        Check if the soccer product is present in the list of products and that more than one product is present.
        """
        return len(products) > 1

    def get_price_ids(self, products, frequency, first_chosen_product):
        price_ids = []
        use_discounted_prices = self.use_discounted_prices(products)

        logger.info(
            f"Gathering price ids with discounted prices: {use_discounted_prices}"
        )

        for product in products:
            use_discounted_prices = self.use_discounted_prices(products)

            if product == first_chosen_product:
                logger.info(
                    f"First chosen product: {product.get_name_display()}, fetching non-discounted price"
                )
                use_discounted_prices = False

            price = product.get_price_id_for_subscription(
                frequency, use_discounted_prices
            )
            logger.info(
                f"Fetched price: {price}, for product: {product.get_name_display()}"
            )
            price_ids.append(price)

        return price_ids


class CreatePredictionCheckoutUrl(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return reverse("accounts:login")

        prediction_id = self.kwargs["prediction_id"]
        prediction = Prediction.objects.get(id=prediction_id)

        if not prediction:
            messages.error(self.request, "Prediction not found.")
            return reverse("core:home")

        service = StripeCheckoutService()
        checkout_session = service.create_onetime_prediction_checkout_session(
            self.request.user, prediction
        )

        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.initiate_checkout(prediction.product, 9.99)
        except Exception as e:
            logger.error(
                f"Error while sending InitiateCheckout Facebook Pixel event: {e}"
            )

        return checkout_session.url


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


class UpdateSubscriptionView(APIView):
    def __init__(self):
        super().__init__()
        self.service = StripeCheckoutService()

    class InputSerializer(serializers.Serializer):
        products = serializers.ListField(child=serializers.IntegerField())
        frequency = serializers.ChoiceField(choices=UserSubscription.Frequency)
        firstProduct = serializers.IntegerField(allow_null=True)

    def use_discounted_prices(self, products):

        return len(products) > 1

    def post(self, request, *args, **kwargs):
        # Check if the user has an active subscription
        if not request.user.subscription_is_active:
            logger.info(
                f"User {request.user.id} attempted to manage subscription without an active subscription."
            )
            return Response(
                status=403,
                data={"message": "The user does not have an active subscription."},
            )

        # Validate input data
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_ids = serializer.validated_data["products"]
        desired_frequency = serializer.validated_data["frequency"]

        # Fetch requested products
        products = Product.objects.filter(id__in=product_ids)
        first_chosen_product = Product.objects.filter(
            id=serializer.validated_data["firstProduct"]
        ).first()
        if len(products) != len(product_ids):
            return Response(
                status=400, data={"message": "One or more product IDs are invalid."}
            )

        if (
                serializer.validated_data["firstProduct"]
                not in serializer.validated_data["products"]
        ):
            return Response(
                status=400, data={"message": "Invalid 'firstProduct' field."}
            )

        if not products.exists():
            return Response(status=400, data={"message": "No products found."})

        # Get the user's current subscription
        user_subscription = request.user.subscription
        stripe_subscription = self.service.get_stripe_subscription_by_id(
            user_subscription.stripe_subscription_id
        )

        # Build price-to-product mapping
        all_products = Product.objects.all()
        price_to_product = {}
        for product in all_products:
            price_to_product[product.monthly_price_stripe_id] = product
            price_to_product[product.yearly_price_stripe_id] = product
            # Include discounted prices if they exist
            if product.discounted_monthly_price_stripe_id:
                price_to_product[product.discounted_monthly_price_stripe_id] = product
            if product.discounted_yearly_price_stripe_id:
                price_to_product[product.discounted_yearly_price_stripe_id] = product

        # Determine desired price IDs based on frequency
        desired_price_ids = {}
        for product in products:
            use_discounted_prices = self.use_discounted_prices(products)

            if product == first_chosen_product:
                logger.info(
                    f"First chosen product: {product.get_name_display()}, fetching non-discounted price"
                )
                use_discounted_prices = False
            desired_price_ids[product] = product.get_price_id_for_subscription(
                desired_frequency, use_discounted_prices
            )

        # Process current subscription items
        current_items = stripe_subscription["items"]["data"]
        items_to_update = []
        covered_products = set()

        logger.info(f"Current items: {current_items}")
        logger.info(f"Desired price ids: {desired_price_ids}")
        logger.info(f"Price to product: {price_to_product}")

        for item in current_items:
            price_id = item["price"]["id"]
            logger.info(f"Processing item with price id: {price_id}")

            product = price_to_product.get(price_id)
            logger.info(f"Matched price id to product: {product.get_name_display()}")
            if product and product in products:
                # Product remains in subscription, update price if frequency changed
                logger.info(
                    f"Product {product.get_name_display()} remains in subscription"
                )
                desired_price_id = desired_price_ids[product]
                logger.info(
                    f"Product {product.get_name_display()}'s desired price id: {desired_price_id}"
                )
                items_to_update.append({"id": item["id"], "price": desired_price_id})
                covered_products.add(product)
            else:
                # Product removed, delete the item
                logger.info(
                    f"Product {product.get_name_display()} removed from subscription"
                )
                items_to_update.append({"id": item["id"], "deleted": True})

        # Add new items for products not currently in subscription
        for product in set(products) - covered_products:
            items_to_update.append({"price": desired_price_ids[product]})

        try:
            self.service.modify_stripe_subscription(
                user_subscription.stripe_subscription_id, items_to_update
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


class SubscriptionPaymentSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        messages.success(
            self.request,
            'You are now subscribed. You can manage your plan in the "Manage Plan" section.',
        )

        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.subscribe(
                self.request.user.subscription.products.all(),
                self.request.user.subscription.price,
            )
        except Exception as e:
            logger.error(f"Error while sending Subscribe Facebook Pixel event: {e}")

        return reverse("accounts:my_account")


class PurchasePaymentSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        prediction_pk = self.kwargs["prediction_pk"]
        prediction = Prediction.objects.prefetch_related(
            "match", "match__home_team", "match__away_team"
        ).get(pk=prediction_pk)

        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.purchase(prediction, 9.99)
        except Exception as e:
            logger.error(f"Error while sending Purchase Facebook Pixel event: {e}")

        return reverse("core:detailed_prediction", kwargs={"pk": prediction_pk})


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
