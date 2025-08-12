import logging

from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserSubscription
from ai_assistant.models import Message
from ai_assistant.v2.ai_service import AiService
from core.models import Product

logger = logging.getLogger(__name__)


class SendMessageToAiView(APIView):
    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        """Serializer for validating incoming message data."""

        message = serializers.CharField()
        timezone = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        """Serializer for formatting the outgoing response."""

        message = serializers.CharField()
        direction = serializers.ChoiceField(choices=Message.Direction)

    def get_user_subscription(self):
        if (
                not self.request.user.is_authenticated
                or not self.request.user.subscription_is_active
        ):
            return None

        return {
            "products": [
                product.id for product in self.request.user.subscription.products.all()
            ],
            "frequency": self.request.user.subscription.frequency,
            "firstProduct": self.request.user.subscription.first_chosen_product.id,
            "productPrice": Product.objects.get(
                name=Product.Names.AI_ANALYST
            ).get_price_for_subscription(
                self.request.user.subscription.frequency, True
            ),
        }

    def post(self, request):
        """Send a message to the AI assistant."""
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # if not self.validate_subscription(request):
        #     return Response(
        #         {
        #             "message": "You need to subscribe to the AI Assistant product to use this feature.",
        #             "user_subscription": self.get_user_subscription(),
        #         },
        #         status=403,
        #     )

        try:
            timezone.activate(serializer.validated_data["timezone"])
        except Exception as e:
            logger.error(
                f"Error activating timezone for User ({request.user.id}): {request.user.username} - {e}"
            )

        message = serializer.validated_data["message"]
        logger.info(
            f"User ({request.user.id}): {request.user.username} has sent a message to the AI assistant"
        )

        ai_service = AiService()
        try:
            response = ai_service.run(message, request.user)
        except Exception:
            logger.exception(
                f"Error processing AI request for User ({request.user.id}): {request.user.username}",
            )
            raise

        logger.info(
            f"AI Response for User ({request.user.id}): {request.user.username} - {response}"
        )

        timezone.deactivate()

        return Response(
            {
                "message": response,
                "direction": Message.Direction.INBOUND,
            }
        )

    def validate_subscription(self, request):
        user = request.user
        if not user.is_authenticated:
            return False

        user_subscription = UserSubscription.objects.filter(
            user=request.user,
            products__name=Product.Names.AI_ANALYST,
            status=UserSubscription.Status.ACTIVE,
        ).first()

        msg_count = Message.objects.filter(
            user=user, direction=Message.Direction.OUTBOUND
        ).count()

        if not user_subscription and msg_count >= 3:
            logger.warning(
                f"User ({user.id}): {user.username} does not have a plan, and has already sent {msg_count} messages."
            )
            return False

        return True


class GetSentMessagesCount(APIView):
    class OutputSerializer(serializers.Serializer):
        """Serializer for formatting the outgoing response."""

        count = serializers.IntegerField()
        can_send = serializers.BooleanField()

    def get(self, request):
        if not request.user.is_authenticated:
            data = {
                "count": 0,
                "can_send": False,
            }
            serializer = self.OutputSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status=200)

        count = Message.objects.filter(
            user=request.user, direction=Message.Direction.OUTBOUND
        ).count()
        can_send = self.validate_subscription(request)

        data = {
            "count": count,
            "can_send": can_send,
        }

        serializer = self.OutputSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

    def validate_subscription(self, request):
        user = request.user
        if not user.is_authenticated:
            return False

        user_subscription = UserSubscription.objects.filter(
            user=request.user,
            products__name=Product.Names.AI_ANALYST,
            status=UserSubscription.Status.ACTIVE,
        ).first()

        msg_count = Message.objects.filter(
            user=user, direction=Message.Direction.OUTBOUND
        ).count()

        if not user_subscription and msg_count >= 3:
            logger.warning(
                f"User ({user.id}): {user.username} does not have a plan, and has already sent {msg_count} messages."
            )
            return False

        return True
