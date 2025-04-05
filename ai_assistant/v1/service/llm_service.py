import logging
import random
from typing import List, Optional

from django.conf import settings
from django.utils import timezone
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from accounts.models import User
from ai_assistant.models import Message
from ai_assistant.v1.service.conversation_history_fetcher import (
    ConversationHistoryFetcher,
)
from ai_assistant.v1.service.input_extractors.league_extractor import LeagueExtractor
from ai_assistant.v1.service.input_extractors.team_extractor import TeamExtractor
from ai_assistant.v1.service.match_context_builder import MatchContextBuilder
from ai_assistant.v1.service.message_classifier import MessageClassifier, MessageCategory
from core.models import SportMatch, Product
from core.services.football_api_service import allowed_league_ids

logger = logging.getLogger(__name__)


class LLMService(MatchContextBuilder):
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, temperature=0)
        self.match_context_builder = MatchContextBuilder()
        self.classifier = MessageClassifier(self.llm)
        self.team_extractor = TeamExtractor(self.llm)
        self.league_extractor = LeagueExtractor(self.llm)
        self.history_fetcher = ConversationHistoryFetcher()
        self.prediction_prompt = SystemMessage(
            content="""
                    You are a professional sports analyst specializing in match analysis and betting predictions. Your task is to provide an engaging and insightful analysis of the specified sports match, tailored for a sports betting audience. Use the provided match data, which includes historical results and prediction metrics, to support your analysis.

                    **Structure your response as follows:**

                    1. **Introduction:**
                       - Start with an exciting and attention-grabbing introduction to the match. Highlight the significance of the game and set the stage for the analysis.

                    2. **Team Analysis:**
                       - For each team, provide a breakdown that includes:
                         - Their approach to the match.
                         - Any concerns or weaknesses.
                         - Insights into their recent performance and form, using the provided match data to highlight relevant statistics (e.g., recent wins, clean sheets, goal-scoring trends).
                       - Use subheadings for each team to clearly separate the analysis.
                       - Incorporate relevant historical data, such as head-to-head records, where appropriate.

                    3. **Betting Picks:**
                       - Provide specific betting picks based on your analysis, such as 'Team A to Win & Over 1.5 Goals' or 'Under 2.5 Goals.'
                       - Highlight one pick as the "Strongest Pick."
                       - List additional picks as "Other Smart Picks."
                       - Use bullet points or numbered lists for clarity.

                    **Guidelines:** 
                        - Use headers for sections and subheadings for clarity.
                        - Employ bold and italic text to emphasize key points.
                        - Incorporate emojis to make the text engaging.
                        - Use tables for presenting data, such as team form or head-to-head records.
                        - Ensure your insights are data-driven and professional.
                        - Do not include concluding statements about the basis of your analysis or additional advice beyond the prediction.
                """
        )

        # Map categories to handler methods
        self.handlers = {
            MessageCategory.MATCH_SPECIFIC_REQUEST: self._handle_match_specific,
            MessageCategory.BET_SUGGESTIONS: self._handle_bet_suggestion,
            MessageCategory.GENERAL_SPORT_INFORMATION: self._handle_general_sport,
        }

    def generate_response(self, user: User, message: str) -> str:
        """Generate a response for the given message."""
        history = self.history_fetcher.fetch(user)

        Message.objects.create(
            message=message, direction=Message.Direction.OUTBOUND, user=user
        )

        logger.info(f"Fetched user history for user: {user.username} (ID: {user.id})")

        category, sport_name = self.classifier.classify(message, history)
        logger.info(f"Message category: {category}, Sport: {sport_name}")
        handler = self.handlers.get(category)

        if handler:
            response = handler(user, message, history, sport_name)
            Message.objects.create(
                message=response, direction=Message.Direction.INBOUND, user=user
            )

            return response

        return "I specialize in sport match analysis and predictions. Please provide a specific match or a general sports question."

    def _handle_general_sport(
            self, user: User, message: str, history: List, sport: Optional[str]
    ) -> str:
        """Handle general sports information requests."""
        try:
            system_message = SystemMessage(
                content="You are a sports expert. Provide general information based on the user's query, considering the conversation history."
            )
            human_message = HumanMessage(content=message)
            response = self.llm.invoke([system_message] + history + [human_message])
            return response.content
        except Exception as e:
            logger.error(f"Error generating general sport response: {e}")
            return "Sorry, I couldn't process your request."

    def _handle_bet_suggestion(
            self, user: User, message: str, history: List, sport: Optional[str]
    ) -> str:
        """Handle general betting suggestion requests."""
        try:
            product_name = sport.upper() if sport else Product.Names.SOCCER
            # Extract the league from the message and history using LeagueExtractor
            extracted_league = self.league_extractor.extract(message, history, sport)
            now = timezone.now()

            if extracted_league:
                upcoming_matches = list(
                    SportMatch.objects.filter(
                        league=extracted_league, kickoff_datetime__gte=now
                    ).order_by("kickoff_datetime")[:20]
                )

                if not upcoming_matches:
                    return f"No upcoming matches found for the league: {extracted_league.name} ({extracted_league.country.name})."

            else:
                upcoming_matches = list(
                    SportMatch.objects.filter(
                        product__name=Product.Names.SOCCER,
                        league__external_id__in=allowed_league_ids,
                        kickoff_datetime__gte=now,
                    ).order_by("kickoff_datetime")[:20]
                )

            if not upcoming_matches:
                return "No upcoming matches found for the specified sport."

            selected_matches = random.sample(
                upcoming_matches, min(3, len(upcoming_matches))
            )

            teams = set()
            for match in selected_matches:
                teams.add(match.home_team)
                teams.add(match.away_team)
            teams = list(teams)

            context = self._build_match_context(teams)

            system_message = SystemMessage(
                content="""
                You are a professional sports analyst specializing in betting predictions. Your task is to provide betting suggestions for the specified upcoming matches, using the provided data.

                For each match, provide:
                - A brief analysis
                - Betting picks, including a "Strongest Pick" and "Other Smart Picks"

                Structure your response as follows:
                - **Match: [Home Team] vs [Away Team] on [date]**
                  - **Analysis**: [brief analysis]
                  - **Betting Picks**:
                    - Strongest Pick: [pick]
                    - Other Smart Picks: [pick1, pick2, ...]

                Use markdown formatting with headers and bullet points for clarity.
                Base your analysis and picks on the provided match data.
                """
            )

            # Create human message with match list and context
            match_list = "\n".join(
                [
                    f"- {match.home_team.name} vs {match.away_team.name} on {match.kickoff_datetime.date()}"
                    for match in selected_matches
                ]
            )
            human_message = HumanMessage(
                content=f"User query: {message}\n\nPlease provide betting suggestions for the following matches:\n{match_list}\n\nMatch data:\n{context}"
            )

            # Generate response from the language model
            response = self.llm.invoke([system_message] + history + [human_message])
            return response.content

        except Exception as e:
            logger.error(f"Error generating bet suggestion response: {e}")
            return "Sorry, I couldn't process your request. Something went wrong—let's try again later!"

    def _handle_match_specific(
            self, user: User, message: str, history: List, sport: Optional[str]
    ) -> str:
        """Handle match-specific requests (analysis or predictions)."""
        try:
            teams = self.team_extractor.extract(message, history, sport)
            if not teams:
                return "Please provide the sport match you are referring to again, with the full team names."

            context = self._build_match_context(teams)

            human_message = HumanMessage(
                content=f"User query: {message}\n\nMatch data:\n{context}"
            )
            response = self.llm.invoke(
                [self.prediction_prompt] + history + [human_message]
            )
            return response.content
        except Exception as e:
            logger.error(f"Error generating match-specific response: {e}")
            return "Sorry, I couldn't process your request."
