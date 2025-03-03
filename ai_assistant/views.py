import logging

from django.conf import settings
from openai import OpenAI
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_assistant.models import Message

logger = logging.getLogger(__name__)


# Create your views here.
class SendMessageToAiView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    class InputSerializer(serializers.Serializer):
        message = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        message = serializers.CharField()

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        message = input_serializer.validated_data["message"]

        outbound_message = Message.objects.create(
            message=message,
            direction=Message.Direction.OUTBOUND,
            user=self.request.user,
        )

        response = self.generate_prompt(message)

        inbound_message = Message.objects.create(
            message=response,
            direction=Message.Direction.INBOUND,
            user=self.request.user,
        )

        output_serializer = self.OutputSerializer(data={"message": response})
        output_serializer.is_valid(raise_exception=True)

        return Response(output_serializer.data)

    def generate_prompt(self, message):
        logger.info(
            f"Generating prompt for message: {message}, for user: {self.request.user.id}"
        )
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI Analyst for Smore, specializing in soccer, basketball, and NFL match analysis and predictions. Respond only to queries about these sports' match analysis, predictions, team/player stats, and betting odds. For future matches, provide analysis based on historical data, recent form, and general trends, noting that real-time factors (e.g., injuries, tactics) may affect the outcome closer to the date. For topics outside these sports or categories, say: 'I focus on soccer, basketball, and NFL. How can I assist with sports?' Maintain a professional tone and base responses on team form, head-to-head records, injuries, tactics, and historical data. For betting odds, give a general sense but direct users to Smore for specifics. No real-time data; avoid speculation without basis. Example: User: 'Analyze Barcelona vs Real Madrid on March 4, 2025.' Assistant: 'Based on historical performance, Barcelona has often dominated recent Clásicos, but Real Madrid’s tactical adjustments could make it close. Barcelona slightly favored based on trends. Check Smore for odds closer to the date.'",
                },
                {"role": "user", "content": message},
            ],
        )

        logger.info(f"Tokens used: {completion.usage.total_tokens}")
        return completion.choices[0].message.content

    def check_permissions(self, request):
        super().check_permissions(request)
