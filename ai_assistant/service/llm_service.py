import logging
from typing import List

from django.conf import settings
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from accounts.models import User
from ai_assistant.models import Message
from ai_assistant.service.conversation_history_fetcher import ConversationHistoryFetcher
from ai_assistant.service.message_classifier import MessageCategory, MessageClassifier
from ai_assistant.service.team_extractor import TeamExtractor
from core.models import SportTeam, SportMatch

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, temperature=0)
        self.team_extraction_prompt = PromptTemplate(
            input_variables=["message"],
            template="""
            Extract the full names of sports teams mentioned in the following message.
            Team names might be in the format "Team A vs Team B" or mentioned separately.
            Provide the full names as a comma-separated list. If no teams are mentioned, respond with "No teams found."

            Examples:
            - Message: "What's the score between Barcelona and Manchester United?"
              Response: "Barcelona, Manchester United"
            - Message: "Tell me about the Lakers game."
              Response: "Los Angeles Lakers"
            - Message: "Who won the match?"
              Response: "No teams found."

            Message: {message}
            Response:
            """,
        )

        # Initialize components
        self.classifier = MessageClassifier(self.llm)
        self.team_extractor = TeamExtractor(self.llm, self.team_extraction_prompt)
        self.history_fetcher = ConversationHistoryFetcher()

        # Map categories to handler methods
        self.handlers = {
            MessageCategory.MATCH_SPECIFIC_REQUEST: self._handle_match_specific,
            MessageCategory.GENERAL_SPORT_INFORMATION: self._handle_general_sport,
        }

    def generate_response(self, user: User, message: str) -> str:
        """Generate a response for the given message."""
        history = self.history_fetcher.fetch(user)

        Message.objects.create(
            message=message, direction=Message.Direction.OUTBOUND, user=user
        )

        # print the history
        for h in history:
            print(h.content)

        logger.info(f"Fetched user history for user: {user.username} (ID: {user.id})")

        category, sport_name = self.classifier.classify(message, history)
        logger.info(f"Message category: {category}, Sport: {sport_name}")
        handler = self.handlers.get(category)

        if handler:
            response = handler(user, message, history)
            Message.objects.create(
                message=response, direction=Message.Direction.INBOUND, user=user
            )

            return response

        return "Please ask me anything sports-related."

    def _handle_general_sport(self, user: User, message: str, history: List) -> str:
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

    def _handle_match_specific(self, user: User, message: str, history: List) -> str:
        """Handle match-specific requests (analysis or predictions)."""
        try:
            teams, matches = self.team_extractor.extract(message, history)
            if not teams:
                return "I was unable to properly identify the teams in the message."

            context = self._build_match_context(teams)

            system_message = SystemMessage(
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
                    - Use markdown formatting with headers, <strong> tags, and paragraph tags.
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
            logger.error(f"Error generating match-specific response: {e}")
            return "Sorry, I couldn't process your request."

    def _calculate_form(self, matches, team):
        """
        Calculate a team's recent form based on the last 5 matches.

        Args:
            matches: List of SportMatch objects
            team: SportTeam object

        Returns:
            str: Form summary (e.g., "3W-1D-1L, Avg Goals Scored: 1.8, Conceded: 1.2")
        """
        wins = draws = losses = goals_scored = goals_conceded = 0
        for match in matches[:5]:
            if match.home_team == team:
                score = int(match.home_team_score or 0)
                opp_score = int(match.away_team_score or 0)
            else:
                score = int(match.away_team_score or 0)
                opp_score = int(match.home_team_score or 0)
            if score > opp_score:
                wins += 1
            elif score == opp_score:
                draws += 1
            else:
                losses += 1
            goals_scored += score
            goals_conceded += opp_score
        match_count = min(len(matches), 5)
        avg_scored = goals_scored / match_count if match_count > 0 else 0
        avg_conceded = goals_conceded / match_count if match_count > 0 else 0
        return f"{wins}W-{draws}D-{losses}L, Avg Goals Scored: {avg_scored:.1f}, Conceded: {avg_conceded:.1f}"

    def _calculate_head_to_head(self, matches, team_a, team_b):
        """
        Calculate head-to-head summary between two teams based on the last 5 matches.

        Args:
            matches: List of SportMatch objects
            team_a: First SportTeam object
            team_b: Second SportTeam object

        Returns:
            str: Head-to-head summary (e.g., "Team A 2W, Team B 1W, 2D")
        """
        a_wins = b_wins = draws = 0
        for match in matches[:5]:
            if match.home_team == team_a and match.away_team == team_b:
                if match.home_team_score > match.away_team_score:
                    a_wins += 1
                elif match.home_team_score < match.away_team_score:
                    b_wins += 1
                else:
                    draws += 1
            elif match.home_team == team_b and match.away_team == team_a:
                if match.home_team_score > match.away_team_score:
                    b_wins += 1
                elif match.home_team_score < match.away_team_score:
                    a_wins += 1
                else:
                    draws += 1
        return f"{team_a.name} {a_wins}W, {team_b.name} {b_wins}W, {draws}D"

    def _build_match_context(self, teams: List[SportTeam]) -> str:
        """
        Build a context string from team data for sports match analysis and betting predictions.

        Args:
            teams: List of SportTeam objects

        Returns:
            str: Formatted context string with team form, past/future matches, and head-to-head data
        """
        from django.utils import timezone
        from django.db.models import Q

        now = timezone.now()
        context = ""

        # Team-specific data
        for team in teams:
            # Fetch past matches (last 5)
            past_matches = SportMatch.objects.filter(
                Q(home_team=team) | Q(away_team=team), kickoff_datetime__lt=now
            ).order_by("-kickoff_datetime")[:5]

            # Fetch future matches (next 2)
            future_matches = SportMatch.objects.filter(
                Q(home_team=team) | Q(away_team=team), kickoff_datetime__gte=now
            ).order_by("kickoff_datetime")[:2]

            context += f"Team {team.name}:\n"

            # **Recent Form**
            form_summary = self._calculate_form(past_matches, team)
            context += f"Recent form (last 5): {form_summary}\n"

            # **Past Matches**
            if past_matches:
                context += "Past matches (most recent first):\n"
                for i, match in enumerate(past_matches):
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    label = "Most recent match" if i == 0 else ""
                    context += f"- {label}: Played vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()} with result {result}\n"
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

            # **Future Matches**
            if future_matches:
                context += "Future matches (soonest first):\n"
                for i, match in enumerate(future_matches):
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    label = "Next match" if i == 0 else ""
                    context += f"- {label}: Will play vs {opponent.name} in league {match.league.name} on {match.kickoff_datetime.date()}\n"
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

        # **Head-to-Head Section** (for two teams)
        if len(teams) == 2:
            team_a, team_b = teams

            # Past head-to-head (last 5)
            head_to_head_past = SportMatch.objects.filter(
                (
                        Q(home_team=team_a, away_team=team_b)
                        | Q(home_team=team_b, away_team=team_a)
                ),
                kickoff_datetime__lt=now,
            ).order_by("-kickoff_datetime")[:5]

            if head_to_head_past:
                context += f"Head-to-head summary (last 5): {self._calculate_head_to_head(head_to_head_past, team_a, team_b)}\n"
                context += f"Head-to-head last 5 matches between {team_a.name} and {team_b.name}:\n"
                for match in head_to_head_past:
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    context += f"- {match.home_team.name} vs {match.away_team.name} on {match.kickoff_datetime.date()}: {result}\n"
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

            # Future head-to-head (next 2, if they exist)
            head_to_head_future = SportMatch.objects.filter(
                (
                        Q(home_team=team_a, away_team=team_b)
                        | Q(home_team=team_b, away_team=team_a)
                ),
                kickoff_datetime__gte=now,
            ).order_by("kickoff_datetime")[:2]

            if head_to_head_future:
                context += f"Upcoming head-to-head matches between {team_a.name} and {team_b.name}:\n"
                for match in head_to_head_future:
                    context += f"- {match.home_team.name} vs {match.away_team.name} on {match.kickoff_datetime.date()}\n"
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

        logger.info(f"Match context: {context}")
        return context
