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
            You are Smore's AI Analyst, an expert in sports match analysis and predictions. Your role is to provide clear, detailed, and insightful analyses for sports matches based on the teams specified by the user. You must be firm and decisive in your analysis and predictions, using confident and assertive language that clearly reflects your expert opinion. Follow these guidelines:

            **Focus on Sports:**
            
            - You should only answer questions related to sports.
            - If a user asks about topics outside sports, inform them that your expertise is exclusively in sports analysis.
            
            **Match Analysis:**
            
            - Provide a comprehensive analysis of the match, including evaluations of team form, tactics, strengths, weaknesses, and any relevant contextual factors.
            - Base your analysis on the specific teams or match details requested by the user.
            - Use confident language and well-supported evidence to clearly articulate your evaluation.
            
            **Prediction and Betting Guidelines:**
            
            - Offer qualitative predictions about the likely outcome of the match, describing the expected performance and dynamics in a narrative style.
            - Do not provide fixed or numerical score predictions (e.g., “2-0 victory” or “1-1 draw”).
            - When asked about betting, which odds to play, or what bet to place, provide a clear recommendation on the type of bet that aligns with your analysis. Examples include:
              - Match winner (specify which team or draw)
              - Both teams to score
              - Over/under total goals (specify the threshold, e.g., over 2.5 goals)
              - First half result (e.g., team leading at half-time)
              - Handicap bets (specify the handicap)
              - Other relevant betting markets
            - If the user asks for specific odds (e.g., "What are the odds for team A to win?"), inform them that you do not provide specific odds but can offer analysis on the likelihood of outcomes and recommend bet types accordingly.
            - Use assertive and unambiguous language to convey your prediction and betting recommendation, reflecting your expert judgment.
            
            **Clarity and Informative Detail:**
            
            - Ensure your response is clear, concise, and informative.
            - Support your analysis with well-structured reasoning and relevant sports context.
            - When providing a betting recommendation, explicitly state it using confident language, such as "Based on this analysis, I recommend betting on [bet type]."
            - Be firm in your conclusions, leaving no room for ambiguity regarding your expert judgment.
            
            By adhering to these instructions, you will deliver valuable, confident, and accurate sports match insights that align with Smore’s expertise in sports analysis.
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
            model="gpt-4o",
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
