from django.db.models import Q

from ai_assistant.v2.types import SportMatchInsightOutputModel
from core.models import SportMatch, SportTeam


class MatchInsightBuilder:
    """
    A class to build insights for match predictions.
    """

    def __init__(self, sport_match: SportMatch):
        """
        Initializes the MatchInsightBuilder with a SportMatch instance.

        Args:
            sport_match (SportMatch): The match for which insights are to be built.
        """
        self.sport_match = sport_match

    def build_insight(self) -> SportMatchInsightOutputModel:
        pass

    def fetch_match_history(self, team: SportTeam, matches_to_fetch=10) -> list[SportMatch]:
        """
        Fetches the last 'matches_to_fetch' matches for the given team.

        Args:
            team (SportTeam): The team for which to fetch match history.
            matches_to_fetch (int): The number of matches to fetch.

        Returns:
            list[SportMatch]: A list of SportMatch instances representing the team's match history.
        """
        current_match_kickoff = self.sport_match.kickoff_datetime

        matches = SportMatch.objects.filter(
            kickoff_datetime__lt=current_match_kickoff).filter(
            Q(home_team=team) | Q(away_team=team)
        ).order_by("-kickoff_datetime")[:matches_to_fetch]

        return list(matches)

    def fetch_head_to_head_matches(self, team1: SportTeam, team2: SportTeam, matches_to_fetch=10) -> list[SportMatch]:
        """
        Fetches the last 'matches_to_fetch' head-to-head matches between two teams.

        Args:
            team1 (SportTeam): The first team.
            team2 (SportTeam): The second team.
            matches_to_fetch (int): The number of head-to-head matches to fetch.

        Returns:
            list[SportMatch]: A list of SportMatch instances representing the head-to-head match history.
        """
        current_match_kickoff = self.sport_match.kickoff_datetime

        matches = SportMatch.objects.filter(
            kickoff_datetime__lt=current_match_kickoff,
            home_team__in=[team1, team2],
            away_team__in=[team1, team2]
        ).order_by("-kickoff_datetime")[:matches_to_fetch]


        return list(matches)

    def fetch_prediction_statistics(self, team: SportTeam) -> dict:

