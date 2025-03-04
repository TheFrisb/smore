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

        user_subscription = UserSubscription.objects.filter(
            user=self.request.user, products__name=Product.Names.AI_ANALYST
        ).first()
        if not user_subscription:
            return Response(
                {
                    "message": "You need to subscribe to the AI Assistant product to use this feature."
                },
                status=403,
            )

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

    def get_system_context(self, user):
        system_context = """
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

        messages = Message.objects.filter(user=user).order_by("-created_at")[0:9]
        if messages:
            system_context += "\n\n**Recent Messages:**"
            for message in messages:
                if message.direction == Message.Direction.INBOUND:
                    system_context += f"\n\nUser: {message.message}"
                else:
                    system_context += f"\n\nSmore's AI Analyst: {message.message}"

        print(system_context)

        return system_context

    def generate_prompt(self, message):
        logger.info(
            f"Generating prompt for message: {message}, for user: {self.request.user.id}"
        )
        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": self.get_system_context(self.request.user),
                },
                {"role": "user", "content": message},
            ],
        )

        logger.info(f"Tokens used: {completion.usage.total_tokens}")
        return completion.choices[0].message.content

    def check_permissions(self, request):
        super().check_permissions(request)
