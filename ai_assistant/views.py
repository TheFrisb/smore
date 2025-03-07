import logging

from django.conf import settings
from openai import OpenAI
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserSubscription
from ai_assistant.models import Message
from core.models import Product

# Configure logging
logger = logging.getLogger(__name__)


class SendMessageToAiView(APIView):
    """
    API view to handle sending messages to an AI assistant and receiving responses.
    Requires user authentication and an active AI Analyst subscription.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self):
        """Initialize the view with an OpenAI client."""
        super().__init__()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Inner serializer classes
    class InputSerializer(serializers.Serializer):
        """Serializer for validating incoming message data."""

        message = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        """Serializer for formatting the outgoing response."""

        message = serializers.CharField()

    def post(self, request):
        """
        Handle POST requests to send a message to the AI and return its response.

        Args:
            request: The HTTP request containing the user's message.

        Returns:
            Response: The AI's response or an error message.
        """
        # Validate input
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        user_message = input_serializer.validated_data["message"]

        # Check user subscription
        user_subscription = UserSubscription.objects.filter(
            user=request.user, products__name=Product.Names.AI_ANALYST
        ).first()
        if not user_subscription:
            return Response(
                {
                    "message": "You need to subscribe to the AI Assistant product to use this feature."
                },
                status=403,
            )

        # Create outbound message
        outbound_message = Message.objects.create(
            message=user_message,
            direction=Message.Direction.OUTBOUND,
            user=request.user,
        )

        # Generate AI response
        ai_response = self.generate_prompt()

        # Create inbound message
        Message.objects.create(
            message=ai_response,
            direction=Message.Direction.INBOUND,
            user=request.user,
        )

        # Serialize and return response
        output_serializer = self.OutputSerializer(data={"message": ai_response})
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)

    def get_system_context(self, user):
        """
        Provide the system context for the AI assistant.

        Args:
            user: The current user (unused but included for potential future personalization).

        Returns:
            str: The system prompt defining the AI's behavior.
        """
        return """
            You are a sports betting assistant on a website focused on match predictions and analyses. Your role is to help users with sports-related queries, such as match predictions, information about teams and upcoming matches, and advice on betting odds. You should only respond to questions related to sports; if a user asks something non-sports-related, politely inform them you can only assist with sports.

            You have comprehensive knowledge of sports data, including team histories, past match interactions, and historical odds. Use this knowledge to provide detailed and confident answers.

            For questions about upcoming matches, provide details about the teams, their past interactions, and any relevant historical data, presenting it as the most up-to-date information available.

            When making predictions, use your knowledge to analyze the match and provide a betting pick, such as:
            - Which team is likely to win
            - Whether both teams will score
            - The likelihood of a specific team leading at half-time
            - The expected number of goals (e.g., over/under 2.5 goals)
            - Other general betting outcomes (e.g., clean sheet, draw no bet)

            Present your prediction confidently, using phrases that convey a strong opinion based on the available data, such as "is likely to win," "has a strong chance of," or "based on the data, I predict." Your predictions are grounded in historical trends and past performance, providing a solid foundation for your analysis. Avoid giving fixed scores like "2:0" as these are too specific and not realistic for predictions.

            If a user questions your prediction or asks for more details, provide further analysis or reasoning based on the available data to support your pick. If a user asks about the certainty of your prediction, reassure them by highlighting the key factors that support your analysis, such as team form, head-to-head records, or player statistics.

            Do not mention any limitations regarding data access, real-time information, or the unpredictability of sports. Always assume your knowledge is sufficient and current.
            Never mention to the user about the historical data, and its accuracy or performance. Never say sport is unpredictable. Never say to the user that the prediction is based off previous performance or historical data. Never mention the nature of your data of any kind.
            Present your prediction as the most likely outcome based on the available data. Do not mention any possibility of the prediction being wrong. Never say the match is decided on the pitch. Do not provide doubt in your responses.

            Remember to consider the context from up to 6 previous messages between you and the user to better understand and respond to the current query, enhancing the conversational flow. When responding, take into account the user's previous queries and your responses to provide more personalized and relevant advice.
        """

    def generate_prompt(self):
        """
        Generate a prompt for the OpenAI API including conversation history.

        Returns:
            str: The AI's response or an error message if the API call fails.
        """
        logger.info(f"Generating prompt for user: {self.request.user.id}")

        # Retrieve the last 30 messages in chronological order efficiently
        recent_messages = list(
            Message.objects.filter(user=self.request.user).order_by("-created_at")[:30]
        )[::-1]

        # Construct API message list
        api_messages = [
                           {"role": "system", "content": self.get_system_context(self.request.user)},
                       ] + [
                           {
                               "role": (
                                   "user"
                                   if msg.direction == Message.Direction.OUTBOUND
                                   else "assistant"
                               ),
                               "content": msg.message,
                           }
                           for msg in recent_messages
                       ]

        # Call OpenAI API with error handling
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=api_messages,
            )
            logger.info(f"Tokens used: {completion.usage.total_tokens}")
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Sorry, I couldn't process your request at the moment. Please try again later."

    def check_permissions(self, request):
        """
        Enforce permission checks defined in permission_classes.

        Args:
            request: The incoming HTTP request.
        """
        super().check_permissions(request)
