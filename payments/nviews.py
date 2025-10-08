import logging

from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.generic import RedirectView
from google.oauth2 import service_account
from googleapiclient.discovery import build
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    PlatformType,
    PurchasedDailyOffer,
    PurchasedPredictions,
)
from backend import settings
from core.models import Prediction, Ticket
from facebook.services.facebook_pixel import FacebookPixel
from payments.services.stripe.stripe_checkout_service import (
    StripeCheckoutService,
)
from subscriptions.models import Product, UserSubscription

logger = logging.getLogger(__name__)


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
            self.request.user,
            prediction,
            self.request.session.get("is_switzerland", False),
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
            self.request.user, ticket, self.request.session.get("is_switzerland", False)
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
        if not UserSubscription.objects.filter(
            user=self.request.user, is_active=True
        ).exists():
            logger.info(
                f"User: {self.request.user.id} attempted to manage subscription without having an active subscription."
            )
            return reverse("subscriptions:plans")

        service = StripeCheckoutService()
        portal_session = service.create_portal_session(self.request.user)
        return portal_session.url


class SubscriptionPaymentSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        has_sports_product = False
        sport_product_names = [Product.Names.SOCCER, Product.Names.BASKETBALL]

        subscribed_products = []
        total_price = 0

        for subscription in UserSubscription.objects.filter(
            user=self.request.user, is_active=True
        ):
            if subscription.product_price.product.name in sport_product_names:
                has_sports_product = True

            subscribed_products.append(subscription.product_price.product)
            total_price += subscription.product_price.amount

        if has_sports_product:
            messages.success(
                self.request,
                "Welcome to SMORE Premium. Your invitation link for the Premium Channel will be ready soon. Please check your e mail address in 30-60 minutes.",
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
            self.request.user,
            daily_offer,
            self.request.session.get("is_switzerland", False),
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
