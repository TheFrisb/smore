import logging
from datetime import timedelta, date
from itertools import combinations
from typing import List, Optional

from django.db.models import Q, QuerySet
from django.utils import timezone

from ai_assistant.service.processors.base_processor import BaseProcessor
from core.models import SportMatch, SportTeam

logger = logging.getLogger(__name__)


class SportMatchProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="SportMatchProcessor", llm_model=None)

    def process(self, prompt_context):
        """
        Process the prompt context for sport match related queries.
        """

        logger.info(f"Fetching sport matches for prompt context: {prompt_context}")

        filter_date = (
            None
            if not prompt_context.suggested_dates
            else prompt_context.suggested_dates[0]
        )

        matches_context = self._build_match_context(
            prompt_context.team_objs, filter_date=filter_date
        )

        if not matches_context:
            prompt_context.can_proceed = False
            prompt_context.response = "No matches found for the given teams."
            return

        prompt_context.matches_context = matches_context

    def _build_match_context(
            self, teams: List[SportTeam], filter_date: Optional[date] = None
    ) -> str:
        """
        Build a context string from team data for sports match analysis and betting predictions.

        Args:
            teams: List of SportTeam objects
            filter_date: Optional date to filter future matches. If not provided, fetches next 7 days.

        Returns:
            str: Formatted context string with team form, past/future matches, and head-to-head data
        """
        now = timezone.now()
        context = ""

        # **Team-Specific Data**
        for team in teams:
            past_matches = self._get_team_past_matches(team, now)
            future_matches = self._get_team_future_matches(team, now, filter_date)
            context += self._build_team_section(team, past_matches, future_matches)

        # **Head-to-Head Data for All Unique Pairs**
        if len(teams) > 1:
            context += "**Head-to-Head Data:**\n"
            for team_a, team_b in combinations(teams, 2):
                past_h2h = self._get_head_to_head_past_matches(team_a, team_b, now)
                future_h2h = self._get_head_to_head_future_matches(
                    team_a, team_b, now, filter_date
                )

                context += self._build_head_to_head_section(
                    team_a, team_b, past_h2h, future_h2h
                )

        logger.info(f"Match context: {context}")
        return context

    def _get_team_past_matches(self, team: SportTeam, now) -> List[SportMatch]:
        """Fetch past matches for a team (last 5)."""
        return (
            SportMatch.objects.filter(
                Q(home_team=team) | Q(away_team=team), kickoff_datetime__lt=now
            )
            .prefetch_related("home_team", "away_team")
            .order_by("-kickoff_datetime")[:5]
        )

    def _get_team_future_matches(
            self, team: SportTeam, now, filter_date: Optional[date]
    ) -> List[SportMatch]:
        """Fetch future matches for a team with date filtering."""
        query = Q(home_team=team) | Q(away_team=team)
        qs = SportMatch.objects.filter(
            query,
        ).prefetch_related("home_team", "away_team")

        if filter_date:
            qs = qs.filter(kickoff_datetime__date=filter_date)
        else:
            qs = qs.filter(kickoff_datetime__gte=now)

        return list(qs.order_by("kickoff_datetime")[:3])

    def _build_team_section(
            self,
            team: SportTeam,
            past_matches: List[SportMatch],
            future_matches: List[SportMatch],
    ) -> str:
        """Build context section for a single team."""
        context = f"**Team {team.name}:**\n"

        # Recent Form
        form_summary = self._calculate_form(past_matches, team)
        context += f"- Recent form (last 5): {form_summary}\n"

        # Past Matches
        if past_matches:
            context += "- Past matches (most recent first):\n"
            for i, match in enumerate(past_matches):
                opponent = self._get_opponent(match, team)
                result = f"{match.home_team_score} - {match.away_team_score}"
                label = "Most recent match" if i == 0 else ""
                context += self._format_match_line(
                    match, opponent, result, label, indent=2
                )
                if match.metadata:
                    context += self._format_prediction_data(match.metadata, indent=4)

        # Future Matches
        if future_matches:
            context += "- Future matches (soonest first):\n"
            for i, match in enumerate(future_matches):
                opponent = self._get_opponent(match, team)
                label = "Next match" if i == 0 else ""
                context += self._format_future_match_line(
                    match, opponent, label, indent=2
                )
                if match.metadata:
                    context += self._format_prediction_data(match.metadata, indent=4)

        context += "\n"
        return context

    def _get_head_to_head_past_matches(
            self, team_a: SportTeam, team_b: SportTeam, now
    ) -> QuerySet[SportMatch]:
        """Fetch past head-to-head matches between two teams (last 5)."""
        return SportMatch.objects.filter(
            (
                    Q(home_team=team_a, away_team=team_b)
                    | Q(home_team=team_b, away_team=team_a)
            ),
            kickoff_datetime__lt=now,
        ).order_by("-kickoff_datetime")[:5]

    def _get_head_to_head_future_matches(
            self, team_a: SportTeam, team_b: SportTeam, now, filter_date: Optional[date]
    ) -> List[SportMatch]:
        """Fetch future head-to-head matches with date filtering."""
        query = Q(home_team=team_a, away_team=team_b) | Q(
            home_team=team_b, away_team=team_a
        )
        qs = SportMatch.objects.filter(query).prefetch_related("home_team", "away_team")

        if filter_date:
            qs = qs.filter(kickoff_datetime__date=filter_date)
        else:
            end_date = now + timedelta(days=30)
            qs = qs.filter(kickoff_datetime__gte=now, kickoff_datetime__lte=end_date)

        return list(qs.order_by("kickoff_datetime")[:3])

    def _build_head_to_head_section(
            self,
            team_a: SportTeam,
            team_b: SportTeam,
            past_matches: List[SportMatch],
            future_matches: List[SportMatch],
    ) -> str:
        """Build context section for head-to-head between two teams."""
        context = f"\n- **{team_a.name} vs {team_b.name}:**\n"

        # Past Head-to-Head
        if past_matches:
            context += f"  - Past head-to-head summary: {self._calculate_head_to_head(past_matches, team_a, team_b)}\n"
            context += "  - Past matches:\n"
            for i, match in enumerate(past_matches):
                result = f"{match.home_team_score} - {match.away_team_score}"
                label = "Most recent head-to-head match" if i == 0 else ""
                context += self._format_match_line(match, None, result, label, indent=4)
                if match.metadata:
                    context += self._format_prediction_data(match.metadata, indent=6)

        # Future Head-to-Head
        if future_matches:
            context += "  - Upcoming matches:\n"
            for i, match in enumerate(future_matches):
                label = "Next head-to-head match" if i == 0 else ""
                context += self._format_future_match_line(match, None, label, indent=4)
                if match.metadata:
                    context += self._format_prediction_data(match.metadata, indent=6)

        return context

    def _get_opponent(self, match: SportMatch, team: SportTeam) -> SportTeam:
        """Determine the opponent team in a match."""
        return match.away_team if match.home_team == team else match.home_team

    def _format_match_line(
            self,
            match: SportMatch,
            opponent: Optional[SportTeam],
            result: str,
            label: str,
            indent: int,
    ) -> str:
        """Format a past match line for the context."""
        indent_str = " " * indent
        opponent_name = opponent.name if opponent else match.away_team.name
        home_team_name = match.home_team.name
        away_team_name = match.away_team.name
        date_str = match.kickoff_datetime.date()

        if opponent:
            line = f"{indent_str}- {label}: Played vs {opponent_name} in {match.league.name} on {date_str}: {result}\n"
        else:
            line = f"{indent_str}- {label}: {home_team_name} vs {away_team_name} in {match.league.name} on {date_str}: {result}\n"
        return line

    def _format_future_match_line(
            self, match: SportMatch, opponent: Optional[SportTeam], label: str, indent: int
    ) -> str:
        """Format a future match line for the context."""
        indent_str = " " * indent
        opponent_name = opponent.name if opponent else match.away_team.name
        home_team_name = match.home_team.name
        away_team_name = match.away_team.name
        date_str = match.kickoff_datetime.date()

        if opponent:
            line = f"{indent_str}- {label}: Will play vs {opponent_name} in {match.league.name} on {date_str}\n"
        else:
            line = f"{indent_str}- {label}: {home_team_name} vs {away_team_name} in {match.league.name} on {date_str}\n"
        return line

    def _format_prediction_data(self, metadata: dict, indent: int = 0) -> str:
        """Format prediction data into a readable string."""
        indent_str = " " * indent
        context = f"{indent_str}Prediction data:\n"

        # check if metadata django json field is empty
        if not metadata:
            context += f"{indent_str}  - No prediction data available.\n"
            return context

        if "winner" in metadata and metadata["winner"]:
            winner = metadata["winner"]

            context += f"{indent_str}  - Predicted winner: {winner.get('name', 'N/A')} ({winner.get('comment', 'N/A')})\n"
        if "percent" in metadata:
            percent = metadata["percent"]
            context += f"{indent_str}  - Win probabilities: Home {percent.get('home', 'N/A')}, Draw {percent.get('draw', 'N/A')}, Away {percent.get('away', 'N/A')}\n"
        if "advice" in metadata:
            context += f"{indent_str}  - Betting advice: {metadata['advice']}\n"
        if "goals" in metadata:
            goals = metadata["goals"]
            context += f"{indent_str}  - Predicted goals: Home {goals.get('home', 'N/A')}, Away {goals.get('away', 'N/A')}\n"
        if "under_over" in metadata and metadata["under_over"] is not None:
            context += (
                f"{indent_str}  - Under/Over prediction: {metadata['under_over']}\n"
            )
        if "win_or_draw" in metadata:
            context += f"{indent_str}  - Win or draw: {'Yes' if metadata['win_or_draw'] else 'No'}\n"
        return context

    def _calculate_form(self, matches: List[SportMatch], team: SportTeam) -> str:
        """Calculate a team's recent form based on the last 5 matches."""
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

    def _calculate_head_to_head(
            self, matches: List[SportMatch], team_a: SportTeam, team_b: SportTeam
    ) -> str:
        """Calculate head-to-head summary between two teams based on the last 5 matches."""
        a_wins = b_wins = draws = 0
        for match in matches[:5]:
            home_team_a = match.home_team == team_a
            if home_team_a and match.away_team == team_b:
                home_score = match.home_team_score
                away_score = match.away_team_score
            else:  # Match is team_b (home) vs team_a (away)
                home_score = (
                    match.away_team_score
                )  # Team_a is away, use their score as "home" for comparison
                away_score = match.home_team_score

            if home_score > away_score:
                a_wins += 1
            elif home_score < away_score:
                b_wins += 1
            else:
                draws += 1
        return f"{team_a.name} {a_wins}W, {team_b.name} {b_wins}W, {draws}D"
