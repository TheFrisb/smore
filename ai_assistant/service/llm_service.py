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
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="o3-mini-2025-01-31"
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
            Extract the full names of sports teams mentioned in the following message as to how they are presented on betting websites. For example 'Sporting' would be 'Sporting CP'. Expand any abbreviations or shortened names to their full form. For example, 'man utd' should be 'Manchester United', 'barca' should be 'Barcelona'. Provide the full names as a comma-separated list.
    
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
            MessageCategory.SPORT_MATCH_PREDICTION: self._handle_analysis,
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
                content="""
                        You are a professional sports analyst specializing in match analysis and betting predictions. Your task is to provide an engaging and insightful analysis of the specified sports match, tailored for a sports betting audience. Use the provided match data, which includes historical results and prediction metrics, to support your analysis.
            
                        **Structure your response as follows:**
            
                        1. **Introduction:**
                           - Start with an exciting and attention-grabbing introduction to the match. Highlight the significance of the game and set the stage for the analysis.
            
                        2. **Team Analysis:**
                           - For each team, provide a breakdown that includes:
                             - Their approach to the match.
                             - Key players to watch.
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
                        - Use markdown formatting with headers, <strong> tags, and paragraph tags.
                        - You may use lists for the betting picks section.
                        - Incorporate emojis or other formatting to make the text visually appealing.
                        - Ensure your insights are data-driven and professional.
                        - Do not include concluding statements about the basis of your analysis or additional advice beyond the prediction.
                """
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

        # Organize matches by team and time (past/future)
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

        # Build the context string
        context = ""
        for team in teams:
            context += f"Team {team.name}:\n"
            past_matches = team_matches[team]["past"]
            future_matches = team_matches[team]["future"]

            # Past matches
            if past_matches:
                context += "Past matches:\n"
                for match in past_matches:
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    context += f"- Played vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()} with result {result}\n"

            # Future matches with prediction data
            if future_matches:
                context += "Future matches:\n"
                for match in future_matches:
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    context += f"- Will play vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()}\n"

                    # Include prediction data if available
                    if match.metadata:
                        prediction_data = match.metadata
                        context += "  Prediction data:\n"
                        if "winner" in prediction_data and prediction_data["winner"]:
                            winner = prediction_data["winner"]
                            context += f"    - Predicted winner: {winner.get('name', 'N/A')} ({winner.get('comment', 'N/A')})\n"
                        if "percent" in prediction_data:
                            percent = prediction_data["percent"]
                            context += f"    - Win probabilities: Home {percent.get('home', 'N/A')}, Draw {percent.get('draw', 'N/A')}, Away {percent.get('away', 'N/A')}\n"
                        if "advice" in prediction_data:
                            context += (
                                f"    - Betting advice: {prediction_data['advice']}\n"
                            )
                        if "goals" in prediction_data:
                            goals = prediction_data["goals"]
                            context += f"    - Predicted goals: Home {goals.get('home', 'N/A')}, Away {goals.get('away', 'N/A')}\n"
                        if (
                                "under_over" in prediction_data
                                and prediction_data["under_over"] is not None
                        ):
                            context += f"    - Under/Over prediction: {prediction_data['under_over']}\n"
                        if "win_or_draw" in prediction_data:
                            context += f"    - Win or draw: {'Yes' if prediction_data['win_or_draw'] else 'No'}\n"

            context += "\n"

        # Head-to-head matches (unchanged)
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
