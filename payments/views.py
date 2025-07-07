import logging
from urllib import request

import stripe
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from google.oauth2 import service_account
from googleapiclient.discovery import build
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    UserSubscription,
    PlatformType,
    PurchasedPredictions,
    PurchasedDailyOffer,
)
from backend import settings
from core.models import Product, Prediction, Ticket
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


class CreateTicketCheckoutUrl(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return reverse("accounts:login")

        ticket_id = self.kwargs["ticket_id"]

        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            messages.error(self.request, "Ticket not found.")
            return reverse("core:home")

        service = StripeCheckoutService()
        checkout_session = service.create_onetime_ticket_checkout_session(
            self.request.user, ticket
        )

        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.initiate_checkout(ticket.product, 9.99)
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
        has_sports_product = False

        for product in self.request.user.subscription.products.all():
            if product.name == Product.Names.SOCCER:
                has_sports_product = True
                break

            if product.name == Product.Names.BASKETBALL:
                has_sports_product = True
                break

        if has_sports_product:
            messages.success(
                self.request,
                'You are now subscribed. We''ve sent a link to your email to join our Telegram Channel. You can manage your plan in the "Manage Plan" section.',
            )
        else:
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


class VerifyMobilePurchaseView(APIView):
    class InputSerializer(serializers.Serializer):
        platform = serializers.ChoiceField(choices=PlatformType)
        purchase_token = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform = serializer.validated_data["platform"]
        purchase_token = serializer.validated_data["purchase_token"]

        if platform == PlatformType.ANDROID:
            prediction_id, is_valid = self.validate_android_purchase(purchase_token)
        elif platform == PlatformType.IOS:
            prediction_id, is_valid = self.validate_ios_purchase(purchase_token)
        else:
            return Response(
                {"message": "Invalid platform."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not is_valid or prediction_id is None:
            return Response(
                {"message": "Invalid purchase token or missing prediction ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prediction = self.get_prediction(prediction_id)
        if not prediction:
            return Response(
                {"message": "Prediction not found."}, status=status.HTTP_404_NOT_FOUND
            )

        PurchasedPredictions.objects.create(
            user=request.user,
            prediction=prediction,
            platform=platform,
        )

        return Response(
            {"message": "Purchase verified successfully."},
            status=status.HTTP_200_OK,
        )

    def validate_android_purchase(self, purchase_token):
        """Validate and consume an Android purchase token, extracting prediction_id."""
        try:
            logger.info(f"Validating Android purchase token: {purchase_token}")
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_KEY_PATH,
                scopes=["https://www.googleapis.com/auth/androidpublisher"],
            )

            android_publisher = build("androidpublisher", "v3", credentials=credentials)

            result = (
                android_publisher.purchases()
                .products()
                .get(
                    packageName=settings.MOBILE_APP_PACKAGE_NAME,
                    productId=settings.MOBILE_PREDICTION_PRODUCT_ID,
                    token=purchase_token,
                )
                .execute()
            )

            if result.get("purchaseState") == 0:
                prediction_id = result.get("obfuscatedExternalAccountId")
                if prediction_id is None:
                    logger.error(
                        "obfuscatedExternalAccountId not found in purchase details."
                    )
                    return None, False
                try:
                    prediction_id = int(prediction_id)
                except ValueError:
                    logger.error(f"Invalid prediction_id: {prediction_id}")
                    return None, False
                logger.info(
                    f"Purchase is valid, consuming it. Prediction ID: {prediction_id}"
                )
                android_publisher.purchases().products().consume(
                    packageName=settings.MOBILE_APP_PACKAGE_NAME,
                    productId=settings.MOBILE_PREDICTION_PRODUCT_ID,
                    token=purchase_token,
                ).execute()
                return prediction_id, True
            else:
                logger.warning(f"Purchase state invalid: {result.get('purchaseState')}")
                return None, False

        except Exception as e:
            logger.error(f"Google Play validation error: {str(e)}")
            return None, False

    def validate_ios_purchase(self, purchase_token):
        """Validate an iOS purchase token and extract prediction_id (placeholder)."""
        # Placeholder for iOS purchase validation logic
        # Replace with actual validation code to extract prediction_id
        try:
            # Example (hypothetical):
            # result = validate_apple_receipt(purchase_token)
            # if result.get("is_valid"):
            #     prediction_id = result.get("applicationUsername")
            #     if prediction_id is None:
            #         logger.error("applicationUsername not found in receipt.")
            #         return None, False
            #     try:
            #         prediction_id = int(prediction_id)
            #     except ValueError:
            #         logger.error(f"Invalid prediction_id: {prediction_id}")
            #         return None, False
            #     return prediction_id, True
            # return None, False
            return None, False  # Placeholder return
        except Exception as e:
            logger.error(f"Apple validation error: {str(e)}")
            return None, False

    def get_prediction(self, prediction_id):
        """Retrieve a Prediction object by ID."""
        try:
            return Prediction.objects.get(id=prediction_id)
        except Prediction.DoesNotExist:
            logger.error(f"Prediction with ID {prediction_id} does not exist.")
            return None


class CreateDailyOfferCheckoutUrl(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return reverse("accounts:login")

        today_date = timezone.now().date()

        if PurchasedDailyOffer.objects.filter(
            user=self.request.user,
            for_date=today_date,
            status=PurchasedDailyOffer.Status.PURCHASED,
        ).exists():
            raise PermissionError(
                f"You've already purchased the daily offer for: {today_date}"
            )

        daily_offer = PurchasedDailyOffer.objects.create(
            user=self.request.user,
            for_date=today_date,
            status=PurchasedDailyOffer.Status.PENDING,
        )

        service = StripeCheckoutService()
        checkout_session = service.create_onetime_daily_offer_checkout_session(
            self.request.user, daily_offer
        )

        try:
            fb_pixel = FacebookPixel(self.request)
            fb_pixel.initiate_checkout(
                Product.objects.filter(name=Product.Names.SOCCER).first(), 24.99
            )
        except Exception as e:
            logger.error(
                f"Error while sending InitiateCheckout Facebook Pixel event: {e}"
            )

        return checkout_session.url
