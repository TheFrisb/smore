import logging

from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
)
from rest_framework.views import APIView

from accounts.models import (
    User,
    PurchasedPredictions,
    PlatformType,
    PurchasedTickets,
    PurchasedDailyOffer,
    UserSubscription,
)
from core.exception import UnprocessableEntity
from core.models import Product
from payments.mobile.permissions import RevenuecatTokenPermission
from payments.mobile.services import verify_transaction

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


class SubscriptionWebhookView(APIView):
    authentication_classes = []
    permission_classes = [RevenuecatTokenPermission]

    class InputSerializer(serializers.Serializer):
        id = serializers.CharField(required=True)
        app_user_id = serializers.CharField(required=True)
        entitlement_ids = serializers.ListField(
            child=serializers.CharField(), required=True
        )
        original_transaction_id = serializers.CharField(required=True)
        type = serializers.CharField(required=True)

    def post(self, request, *args, **kwargs):
        logger.info("Received subscription webhook: %s", request.data)
        event_data = request.data.get("event", {})
        serializer = self.InputSerializer(data=event_data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["type"] == "EXPIRATION":
            self._deactivate_subscription(serializer.validated_data["app_user_id"])
        else:
            products = self._get_products_from_entitlements(
                serializer.validated_data["entitlement_ids"]
            )

        return Response(
            status=HTTP_200_OK,
            data={"detail": "Subscription webhook processed successfully"},
        )

    def _get_products_from_entitlements(self, entitlement_ids):
        product_names = []
        for entitlement_id in entitlement_ids:
            logger.info("Processing entitlement_id: %s", entitlement_id)
            if not entitlement_id.startswith("monthly_", "yearly_"):
                continue

            product_name = entitlement_id.split("_", 1)[1].upper().replace("_", " ")
            product_names.append(product_name)

        logger.info("Extracted product names from entitlements: %s", product_names)
        return Product.objects.filter(name__in=product_names)

    def get_user_subscriptions(self, app_user_id):
        try:
            return UserSubscription.objects.get(
                user_id=int(app_user_id),
                provider_type=UserSubscription.ProviderType.REVENUECAT,
            )
        except UserSubscription.DoesNotExist:
            logger.error("User subscription not found for app_user_id: %s", app_user_id)
            raise UnprocessableEntity()

    def _deactivate_subscription(self, app_user_id):
        logger.info("Deactivating subscription for app_user_id: %s", app_user_id)
        user_subscription = self.get_user_subscriptions(app_user_id)
        user_subscription.status = UserSubscription.Status.INACTIVE
        user_subscription.save()
