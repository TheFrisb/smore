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
        self.prediction_llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model_name='o3-2025-04-16')
        self.prediction_llm.bind_tools(
            [
                {
                    "type": "web_search_preview"
                }
            ]
        )
        self.match_context_builder = MatchContextBuilder()
        self.classifier = MessageClassifier(self.llm)
        self.team_extractor = TeamExtractor(self.llm)
        self.league_extractor = LeagueExtractor(self.llm)
        self.history_fetcher = ConversationHistoryFetcher()
        self.prediction_prompt = SystemMessage(
            content="""
            You are an expert football and basketball match analyst working for SMORE, a professional sports research brand known for accurate predictions and smart betting strategies.
            
            Always follow these guidelines, and only answer sport-related questions. If a prompt is not sport related (either directly or inferred meaning through the user's chat history), signal the user that you do not answer such questions.
            
            Consider the user’s previous questions and preferences from their conversation history to tailor your response.
            
            Tone:
            Speak with confidence, professionalism, and expertise. Never sound unsure. Use emojis at the beginning of important sections (e.g., 📊 for stats, 🔍 for insights, 🎯 for most accurate prediction (always put ✅ infront of the picks), 💡 for more betting suggestions).
            
            Match Analysis Format:
            Begin with an intro (match date, importance, and team form).
            Before you start writing about the team forms, write a Introduction text about the match we're about to analyze.
            
            Include:
            - Standings and current team form of both teams (Detailed and Deep Explanation) 
            - Head-to-head records (Detailed and Deep Explanation) 
            - Goals scored/conceded
            - Injuries or key players out
            - Style of play and tactical matchups
            
            Prediction Section:
            End with a betting suggestion named (Best Betting Suggestion), that is most accurate and its probability of success as a percentage (e.g., “Double Chance 1X – 78% chance”), and mention a 4 additional betting suggestions named as (Other valuable betting suggestions:)
            
            Bet Types to Use:
            Suggest markets like:
            - Double Chance (1X, 12, X2)
            - Both Teams to Score (Yes/No)
            - Over/Under Total Goals
            - Total corners  
            - Goalkeeper saves
            - Player to score
            - Team to win either half
            - Team Total Goals (Over/Under 0.5 or 1.5)
            - Double Chance combined with Total goals
            - 1st or 2nd half over/under  0.5 or 1.5 goals
            - 1st half Double Chance (1X, 12 , 2X)
            
            You will also be given precomputed metadata statistics about the match, which you can use to make good betting suggestions.

            Tone for Betting Advice:
            Avoid saying “guaranteed” or “fixed” – use “very likely,” “smart pick,” or “based on research.”
            Mention the word "Stake" when referring to how much to bet.

            Style Preference:
            - Always use (paragraph form) , (never lists). Always use markdown formatting.
            - Always write the text like a professional sports analyst, and make them very interesting for the reader.
            - Always include Headlines and Emojis.
            - Write the text more human-like written, more natural but still professional.
            - Write as if for a Blog match preview.
            - Always write the texts in Paragraphic Style and give longer and detailed explanation about the head to head stands, and current team forms.
            - Use headers for sections and subheadings for clarity.
            - Employ bold and italic text to emphasize key points.
            - Incorporate emojis to make the text engaging.
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

        else:
            response = self.prediction_llm.invoke([self.prediction_prompt] + history + [HumanMessage(content=message)])
            Message.objects.create(
                message=response, direction=Message.Direction.INBOUND, user=user
            )
            return response.content


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
            response = self.prediction_llm.invoke([self.prediction_prompt] + history + [human_message])
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
            response = self.prediction_llm.invoke(
                [self.prediction_prompt] + history + [human_message]
            )
            return response.content
        except Exception as e:
            logger.error(f"Error generating match-specific response: {e}")
            return "Sorry, I couldn't process your request."
