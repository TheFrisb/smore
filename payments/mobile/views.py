import logging

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from rest_framework.views import APIView

from accounts.models import (
    PlatformType,
    PurchasedDailyOffer,
    PurchasedPredictions,
    PurchasedTickets,
    User,
)
from backend import settings
from payments.mobile.permissions import RevenuecatTokenPermission
from payments.mobile.services import verify_transaction
from payments.services.revenuecat.base_revenuecat_service import BaseRevenuecatService
from subscriptions.models import BillingProvider, UserSubscription

logger = logging.getLogger(__name__)


class ConsumablePurchaseWebhookView(APIView):
    authentication_classes = []
    permission_classes = [RevenuecatTokenPermission]

    class InputSerializer(serializers.Serializer):
        app_user_id = serializers.CharField(required=True)
        original_transaction_id = serializers.CharField(required=True)
        presented_offering_id = serializers.CharField(required=True)
        store = serializers.CharField(required=True)
        type = serializers.CharField(required=True)

    def post(self, request, *args, **kwargs):
        event_data = request.data.get("event", {})
        serializer = self.InputSerializer(data=event_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data["type"] != "NON_RENEWING_PURCHASE":
            logger.warning("Received unsupported purchase type: %s", data["type"])
            return Response(
                {"detail": "Unsupported purchase type"},
                status=HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            status=HTTP_200_OK, data={"detail": "Purchase processed successfully"}
        )

    def get_user(self, app_user_id):
        return User.objects.get(id=app_user_id)


class ConsumeConsumableView(APIView):
    class InputSerializer(serializers.Serializer):
        original_transaction_id = serializers.CharField(required=True)
        consumable_type = serializers.ChoiceField(
            choices=["single_prediction", "single_ticket", "daily_offer"], required=True
        )
        purchased_object_id = serializers.IntegerField(required=True)

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        original_transaction_id = data["original_transaction_id"]
        consumable_type = data["consumable_type"]

        if not verify_transaction(original_transaction_id, self.request.user.id):
            logger.error(
                "Transaction verification failed for user %s with transaction %s",
                self.request.user.id,
                original_transaction_id,
            )
            return Response(
                {"detail": "Invalid transaction"}, status=HTTP_422_UNPROCESSABLE_ENTITY
            )

        # if either a prediction or ticket exists with the same original_transaction_id, we should not create a new one

        if consumable_type == "single_prediction":

            if PurchasedPredictions.objects.filter(
                revenuecat_transaction_id=original_transaction_id
            ).exists():
                logger.warning(
                    "Prediction already consumed for transaction %s by user %s",
                    original_transaction_id,
                    self.request.user.username,
                )
                return Response(
                    {"detail": "Prediction already consumed"},
                    status=HTTP_422_UNPROCESSABLE_ENTITY,
                )

            purchased_prediction = PurchasedPredictions.objects.create(
                prediction_id=data["purchased_object_id"],
                user=self.request.user,
                platform=PlatformType.MOBILE,
                revenuecat_transaction_id=original_transaction_id,
            )

            logger.info(
                "Single prediction consumed: %s for user %s",
                purchased_prediction.prediction.match,
                self.request.user.username,
            )

        elif consumable_type == "single_ticket":
            if PurchasedTickets.objects.filter(
                revenuecat_transaction_id=original_transaction_id
            ).exists():
                logger.warning(
                    "Ticket already consumed for transaction %s by user %s",
                    original_transaction_id,
                    self.request.user.username,
                )
                return Response(
                    {"detail": "Ticket already consumed"},
                    status=HTTP_422_UNPROCESSABLE_ENTITY,
                )

            purchased_ticket = PurchasedTickets.objects.create(
                ticket_id=data["purchased_object_id"],
                user=self.request.user,
                revenuecat_transaction_id=original_transaction_id,
            )

            logger.info(
                "Single ticket consumed: %s for user %s",
                purchased_ticket.ticket,
                self.request.user.username,
            )
        else:
            daily_offer = PurchasedDailyOffer.objects.filter(
                for_date=timezone.now().date(),
                status=PurchasedDailyOffer.Status.PURCHASED,
                user=self.request.user,
            ).first()

            if not daily_offer:
                PurchasedDailyOffer.objects.create(
                    user=self.request.user,
                    for_date=timezone.now().date(),
                    status=PurchasedDailyOffer.Status.PURCHASED,
                )

            else:
                logger.warning(
                    "Daily offer already consumed for user %s",
                    self.request.user.username,
                )
                return Response(
                    {"detail": "Daily offer already consumed"},
                    status=HTTP_422_UNPROCESSABLE_ENTITY,
                )

        return Response(status=HTTP_204_NO_CONTENT)


@csrf_exempt
@api_view(["POST"])
def subscription_webhook_view(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")

    if not auth_header.startswith("Bearer "):
        return Response(
            {"detail": "Invalid token header. No credentials provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token = auth_header.split(" ")[1]

    if token != settings.REVENUECAT_TOKEN:
        return Response(
            {"detail": "Invalid token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    service = BaseRevenuecatService()

    event_data = request.data["event"]
    event_type = event_data["type"]
    app_user_id = event_data["app_user_id"]
    external_product_id = event_data["product_id"]

    user = service.get_user(subscription_data=event_data)
    product_price = service.get_product_price(external_product_id)
    purchased_at, expiration_date = service.get_start_and_end_datetimes_from_ms(
        subscription_data=event_data
    )
    subscription_id = service.construct_external_id(user, external_product_id)

    if event_type == "INITIAL_PURCHASE":
        UserSubscription.objects.create(
            user=user,
            product_price=product_price,
            provider=BillingProvider.REVENUECAT,
            start_date=purchased_at,
            end_date=expiration_date,
            provider_subscription_id=subscription_id,
            is_active=True,
        )

    elif event_type == "RENEWAL":
        UserSubscription.objects.filter(
            user=user,
            provider=BillingProvider.REVENUECAT,
            provider_subscription_id=subscription_id,
        ).update(end_date=expiration_date, is_active=True)

    elif event_type == "EXPIRATION":
        UserSubscription.objects.filter(
            provider=BillingProvider.REVENUECAT,
            provider_subscription_id=subscription_id,
        ).update(is_active=False)

    return Response(status=HTTP_204_NO_CONTENT)
