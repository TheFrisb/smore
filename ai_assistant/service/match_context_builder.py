import logging
from itertools import combinations
from typing import List

from django.db.models import Q
from django.utils import timezone

from core.models import SportMatch, SportTeam

logger = logging.getLogger(__name__)


class MatchContextBuilder:
    def _build_match_context(self, teams: List[SportTeam]) -> str:
        """
        Build a context string from team data for sports match analysis and betting predictions.

        Args:
            teams: List of SportTeam objects

        Returns:
            str: Formatted context string with team form, past/future matches, and head-to-head data
        """
        now = timezone.now()
        context = ""

        # **Team-Specific Data**
        for team in teams:
            # Fetch past matches (last 5)
            past_matches = SportMatch.objects.filter(
                Q(home_team=team) | Q(away_team=team), kickoff_datetime__lt=now
            ).order_by("-kickoff_datetime")[:5]

            # Fetch future matches (next 3)
            future_matches = SportMatch.objects.filter(
                Q(home_team=team) | Q(away_team=team), kickoff_datetime__gte=now
            ).order_by("kickoff_datetime")[:3]

            context += f"**Team {team.name}:**\n"

            # Recent Form
            form_summary = self._calculate_form(past_matches, team)
            context += f"- Recent form (last 5): {form_summary}\n"

            # Past Matches
            if past_matches:
                context += "- Past matches (most recent first):\n"
                for i, match in enumerate(past_matches):
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    result = f"{match.home_team_score} - {match.away_team_score}"
                    label = "Most recent match" if i == 0 else ""
                    context += f"  - {label}: Played vs {opponent.name} in {match.league.name} on {match.kickoff_datetime.date()}: {result}\n"
                    if match.metadata:
                        context += self._format_prediction_data(
                            match.metadata, indent=4
                        )

            # Future Matches
            if future_matches:
                context += "- Future matches (soonest first):\n"
                for i, match in enumerate(future_matches):
                    opponent = (
                        match.away_team if match.home_team == team else match.home_team
                    )
                    label = "Next match" if i == 0 else ""
                    context += f"  - {label}: Will play vs {opponent.name} in {match.league.name} on {match.kickoff_datetime.date()}\n"
                    if match.metadata:
                        context += self._format_prediction_data(
                            match.metadata, indent=4
                        )

            context += "\n"

        # **Head-to-Head Data for All Unique Pairs**
        if len(teams) >= 2:
            context += "**Head-to-Head Data:**\n"
            for team_a, team_b in combinations(teams, 2):
                context += f"\n- **{team_a.name} vs {team_b.name}:**\n"

                # Past head-to-head (last 5)
                head_to_head_past = SportMatch.objects.filter(
                    (
                        Q(home_team=team_a, away_team=team_b)
                        | Q(home_team=team_b, away_team=team_a)
                    ),
                    kickoff_datetime__lt=now,
                ).order_by("-kickoff_datetime")[:5]

                if head_to_head_past.exists():
                    context += f"  - Past head-to-head summary: {self._calculate_head_to_head(head_to_head_past, team_a, team_b)}\n"
                    context += "  - Past matches:\n"
                    for i, match in enumerate(head_to_head_past):
                        result = f"{match.home_team_score} - {match.away_team_score}"
                        label = "Most recent head-to-head match" if i == 0 else ""
                        context += f"    - {label}: {match.home_team.name} vs {match.away_team.name} in {match.league.name} on {match.kickoff_datetime.date()}: {result}\n"
                        if match.metadata:
                            context += self._format_prediction_data(
                                match.metadata, indent=6
                            )

                # Future head-to-head (next 2)
                head_to_head_future = SportMatch.objects.filter(
                    (
                        Q(home_team=team_a, away_team=team_b)
                        | Q(home_team=team_b, away_team=team_a)
                    ),
                    kickoff_datetime__gte=now,
                ).order_by("kickoff_datetime")[:2]

                if head_to_head_future.exists():
                    context += "  - Upcoming matches:\n"
                    for i, match in enumerate(head_to_head_future):
                        label = "Next head-to-head match" if i == 0 else ""
                        context += f"    - {label}: {match.home_team.name} vs {match.away_team.name} in {match.league.name} on {match.kickoff_datetime.date()}\n"
                        if match.metadata:
                            context += self._format_prediction_data(
                                match.metadata, indent=6
                            )

        logger.info(f"Match context: {context}")
        return context

    def _format_prediction_data(self, metadata: dict, indent: int = 0) -> str:
        """
        Format prediction data into a readable string.

        Args:
            metadata: Dictionary containing prediction data
            indent: Number of spaces to indent each line

        Returns:
            str: Formatted prediction data string
        """
        indent_str = " " * indent
        context = f"{indent_str}Prediction data:\n"
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
