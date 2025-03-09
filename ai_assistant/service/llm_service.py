# services.py
import logging
from typing import List

from django.conf import settings
from django.db.models import Q
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from accounts.models import User
from ai_assistant.service.conversation_history_fetcher import ConversationHistoryFetcher
from ai_assistant.service.message_classifier import MessageCategory, MessageClassifier
from ai_assistant.service.team_extractor import TeamExtractor
from core.models import SportTeam, SportMatch

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
        )

        self.classification_prompt = PromptTemplate(
            input_variables=["message"],
            template="""
            Classify the following message into one of these categories:
            - sport_match_analysis: The user is asking for an in-depth breakdown of a specific sports match.
            - sport_match_prediction: The user is asking for a prediction for a specific sports match.
            - general_sport_information: The user seeks general sports information, not tied to a specific match.
            - unrelated: The message is not sports-related.

            Message: {message}

            Category:
            """,
        )
        self.team_extraction_prompt = PromptTemplate(
            input_variables=["message"],
            template="""
            Extract the full names of sports teams mentioned in the following message. Expand any abbreviations or shortened names to their full form. For example, 'man utd' should be 'Manchester United', 'barca' should be 'Barcelona'. Provide the full names as a comma-separated list.
    
            Message: {message}
            """,
        )
        self.analysis_prompt = PromptTemplate(
            input_variables=["match_data"],
            template="Analyze the following match: {match_data}",
        )
        self.prediction_prompt = PromptTemplate(
            input_variables=["match_data"],
            template="Predict the outcome of the following match: {match_data}",
        )

        # Initialize components
        self.classifier = MessageClassifier(self.llm, self.classification_prompt)
        self.team_extractor = TeamExtractor(self.llm, self.team_extraction_prompt)
        self.history_fetcher = ConversationHistoryFetcher()

        # Map categories to handler methods
        self.handlers = {
            MessageCategory.GENERAL_SPORT_INFORMATION: self._handle_general_sport,
            MessageCategory.SPORT_MATCH_ANALYSIS: self._handle_analysis,
        }

    def generate_response(self, user: User, message: str) -> str:
        """Generate a response for the given message."""
        category = self.classifier.classify(message)
        handler = self.handlers.get(category)
        if handler:
            return handler(user, message)

        return "Sorry, I can only assist with sports-related queries."

    def _handle_general_sport(self, user: User, message: str) -> str:
        try:
            history = self.history_fetcher.fetch(user)
            system_message = SystemMessage(
                content="You are a sports expert. Provide general information based on the user's query, considering the conversation history."
            )
            human_message = HumanMessage(content=message)
            response = self.llm.invoke([system_message] + history + [human_message])
            return response.content
        except Exception as e:
            logger.error(f"Error generating general sport response: {e}")
            return "Sorry, I couldn't process your request."

    def _handle_analysis(self, user: User, message: str) -> str:
        try:
            history = self.history_fetcher.fetch(user)
            teams, matches = self.team_extractor.extract(message)
            if not teams:
                return "No teams found in the message."

            context = self._build_match_context(teams, matches)

            system_message = SystemMessage(
                content="You are a sports analyst. Provide an in-depth analysis based on the user's query and the provided match data."
            )
            human_message = HumanMessage(
                content=f"User query: {message}\n\nMatch data:\n{context}"
            )
            response = self.llm.invoke([system_message] + history + [human_message])
            return response.content
        except Exception as e:
            logger.error(f"Error generating analysis response: {e}")
            return "Sorry, I couldn't analyze the match."

    def _build_match_context(
            self, teams: List[SportTeam], matches: List[SportMatch]
    ) -> str:
        from django.utils import timezone

        now = timezone.now()

        team_matches = {team: {"past": [], "future": []} for team in teams}
        for match in matches:
            if match.home_team in teams:
                if match.kickoff_datetime < now:
                    team_matches[match.home_team]["past"].append(match)
                else:
                    team_matches[match.home_team]["future"].append(match)
            if match.away_team in teams:
                if match.kickoff_datetime < now:
                    team_matches[match.away_team]["past"].append(match)
                else:
                    team_matches[match.away_team]["future"].append(match)

        context = ""
        for team in teams:
            context += f"Team {team.name}:\n"
            past_matches = team_matches[team]["past"]
            future_matches = team_matches[team]["future"]

            if past_matches:
                context += "Past matches:\n"
                for match in past_matches:
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    context += f"- Played vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()} with result {result}\n"

            if future_matches:
                context += "Future matches:\n"
                for match in future_matches:
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    context += f"- Will play vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()}\n"

            context += "\n"

        if len(teams) == 2:
            team_a, team_b = teams
            head_to_head = SportMatch.objects.filter(
                (Q(home_team=team_a) & Q(away_team=team_b))
                | (Q(home_team=team_b) & Q(away_team=team_a)),
                kickoff_datetime__lt=now,
            ).order_by("-kickoff_datetime")[:10]

            if head_to_head:
                context += f"Head-to-head last 10 matches between {team_a.name} and {team_b.name}:\n"
                for match in head_to_head:
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    context += f"- {match.home_team.name} vs {match.away_team.name} on {match.kickoff_datetime.date()}: {result}\n"
                context += "\n"

        logger.info(f"Match context: {context}")

        return context
