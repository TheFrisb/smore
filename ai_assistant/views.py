import logging

from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_assistant.models import Message
from ai_assistant.utils import AIUsagePolicy
from ai_assistant.v2.ai_service import AiService
from subscriptions.models import (
    BillingInterval,
    BillingProvider,
    Product,
    ProductPrice,
)

logger = logging.getLogger(__name__)


class SendMessageToAiView(APIView):
    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        message = serializers.CharField()
        timezone = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        message = serializers.CharField()
        direction = serializers.ChoiceField(choices=Message.Direction)

    def get_user_subscription_summary(self, user):
        """
        Returns a minimal subscription summary for the client.
        Because your new UserSubscription model doesn't define `frequency` or
        `first_chosen_product`, we only return product ids from active subscriptions.
        If you still need `frequency` and `firstProduct`, add those fields to the new model
        or compute them here from your business rules.
        """
        if not user or not user.is_authenticated:
            return None

        active_subs = user.subscriptions.filter(is_active=True).select_related(
            "product_price__product"
        )
        return {
            "products": [s.product_price.product.id for s in active_subs],
            "active_subscription_count": active_subs.count(),
            "productPrice": ProductPrice.objects.filter(
                product__name=Product.Names.AI_ANALYST,
                interval=BillingInterval.MONTH,
                interval_count=1,
                provider=BillingProvider.STRIPE,
            )
            .first()
            .amount,
            "frequency": "monthly",
        }

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # validate usage
        can_use, current_count = AIUsagePolicy.can_use_ai(request.user)
        if not can_use:
            return Response(
                {
                    "message": "You need to subscribe to the AI Assistant product to use this feature.",
                    "user_subscription": self.get_user_subscription_summary(
                        request.user
                    ),
                    "outbound_messages_sent": current_count,
                    "free_message_limit": (
                        AIUsagePolicy.FREE_MESSAGES_LIMIT
                        if hasattr(AIUsagePolicy, "FREE_MESSAGES_LIMIT")
                        else 3
                    ),
                },
                status=403,
            )

        try:
            timezone.activate(serializer.validated_data["timezone"])
        except Exception as e:
            logger.error(
                f"Error activating timezone for User ({request.user.id}): {request.user.username} - {e}"
            )

        message_text = serializer.validated_data["message"]
        logger.info(
            f"User ({request.user.id}): {request.user.username} has sent a message to the AI assistant"
        )

        ai_service = AiService()
        try:
            response = ai_service.run(message_text, request.user)
        except Exception:
            logger.exception(
                f"Error processing AI request for User ({request.user.id}): {request.user.username}"
            )
            raise

        logger.info(
            f"AI Response for User ({request.user.id}): {request.user.username} - {response}"
        )

        timezone.deactivate()

        return Response({"message": response, "direction": Message.Direction.INBOUND})


class GetSentMessagesCount(APIView):
    permission_classes = [IsAuthenticated]

    class OutputSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        can_send = serializers.BooleanField()

    def get(self, request):
        if not self.request.user.is_authenticated:
            data = {"count": 0, "can_send": False}
            serializer = self.OutputSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)

        count = Message.objects.filter(
            user=self.request.user, direction=Message.Direction.OUTBOUND
        ).count()
        can_send, _ = AIUsagePolicy.can_use_ai(self.request.user)

        data = {"count": count, "can_send": can_send}
        serializer = self.OutputSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
