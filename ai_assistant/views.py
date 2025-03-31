import logging

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserSubscription
from ai_assistant.models import Message
from ai_assistant.service.llm_service import LLMService
from core.models import Product

# Configure logging
logger = logging.getLogger(__name__)


class SendMessageToAiView(APIView):
    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()

    permission_classes = [IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        """Serializer for validating incoming message data."""

        message = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        """Serializer for formatting the outgoing response."""

        message = serializers.CharField()
        direction = serializers.ChoiceField(choices=Message.Direction)

    def post(self, request):
        """Send a message to the AI assistant."""
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self.validate_subscription(request):
            return Response(
                {
                    "message": "You need to subscribe to the AI Assistant product to use this feature."
                },
                status=403,
            )

        message = serializer.validated_data["message"]
        logger.info(
            f"User ({request.user.id}): {request.user.username} has sent a message to the AI assistant"
        )

        response = self.llm_service.generate_response(
            user=request.user, message=message
        )
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

        if not user_subscription:
            return False

        return True
