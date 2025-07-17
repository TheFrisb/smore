from django.db.models import Q
from django.utils import timezone

from ai_assistant.v2.types import SportMatchInsightOutputModel, PredictionStatisticsOutputModel, SportTeamOutputModel, \
    SportMatchOutputModel, TeamStandingOutputModel
from core.models import SportMatch, SportTeam, TeamStanding


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
        """
        Builds insights for the match by fetching relevant data such as team history, upcoming matches,
        head-to-head matches, and prediction statistics.

        Returns:
            SportMatchInsightOutputModel: An instance containing the match insights.
        """
        home_history = self.fetch_matches_by_kickoff_datetime(
            team=self.sport_match.home_team, history=True
        )
        home_future = self.fetch_matches_by_kickoff_datetime(
            team=self.sport_match.home_team, history=False
        )
        away_history = self.fetch_matches_by_kickoff_datetime(
            team=self.sport_match.away_team, history=True
        )
        away_future = self.fetch_matches_by_kickoff_datetime(
            team=self.sport_match.away_team, history=False
        )
        head2head = self.fetch_head_to_head_matches(
            team1=self.sport_match.home_team,
            team2=self.sport_match.away_team
        )
        home_team_standings, away_team_standings = self.get_standings()

        return SportMatchInsightOutputModel(
            match=SportMatchOutputModel.model_validate(self.sport_match),
            home_team_history=home_history,
            away_team_history=away_history,
            home_team_upcoming_matches=home_future,
            away_team_upcoming_matches=away_future,
            head_to_head_matches=head2head,
            prediction_statistics=self.fetch_prediction_statistics(),
            home_team_standings=home_team_standings,
            away_team_standings=away_team_standings

        )

    def fetch_matches_by_kickoff_datetime(self, team: SportTeam, history: bool, matches_to_fetch=10) -> \
            list[SportMatchOutputModel]:
        """
        Fetches the last 'matches_to_fetch' matches for the given team.

        Args:
            team (SportTeam): The team for which to fetch match history.
            history (bool): If True, fetches past matches; if False, fetches future matches.
            matches_to_fetch (int): The number of matches to fetch.

        Returns:
            list[SportMatch]: A list of SportMatch instances representing the team's match history.
        """

        queryset = SportMatch.objects.filter(
            Q(home_team=team) | Q(away_team=team)
        )

        if not history:
            queryset = queryset.filter(kickoff_datetime__gt=timezone.now()).order_by("kickoff_datetime")[
                       :matches_to_fetch]
        else:
            queryset = queryset.filter(kickoff_datetime__lt=timezone.now()).order_by("-kickoff_datetime")[
                       :matches_to_fetch]

        return [SportMatchOutputModel.model_validate(m) for m in queryset]

    def fetch_head_to_head_matches(self, team1: SportTeam, team2: SportTeam, matches_to_fetch=10) -> list[
        SportMatchOutputModel]:
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

        queryset = SportMatch.objects.filter(
            kickoff_datetime__lt=current_match_kickoff
        ).filter(
            Q(home_team=team1, away_team=team2) | Q(home_team=team2, away_team=team1)
        ).order_by("-kickoff_datetime")[:matches_to_fetch]

        return [SportMatchOutputModel.model_validate(m) for m in queryset]

    def fetch_prediction_statistics(self) -> PredictionStatisticsOutputModel:
        """
        Fetches prediction statistics for the match.
        This method extracts various statistics from the match metadata, such as over/under goals,
        suggested advice, and win probabilities for the home and away teams.

        Returns:
            PredictionStatisticsOutputModel: An instance containing the prediction statistics for the match.
        """
        # 1) Load the raw dict (metadata is a JSONField or TextField)
        raw = self.sport_match.metadata or {}
        if not isinstance(raw, dict):
            raw = {}

        # 2) Extract each bit (using .get to avoid KeyErrors)
        goals = raw.get("goals", {})
        percent = raw.get("percent", {})
        winner_info = raw.get("winner", {})

        # 3) Build the “winner” team model, if any
        suggested_winner = None
        winner_id = winner_info.get("id")
        if winner_id:
            if winner_id == self.sport_match.home_team.external_id:
                team_obj = self.sport_match.home_team
            elif winner_id == self.sport_match.away_team.external_id:
                team_obj = self.sport_match.away_team
            else:
                team_obj = None

            if team_obj:
                suggested_winner = SportTeamOutputModel.model_validate(team_obj)

        # 5) Instantiate your Pydantic model
        return PredictionStatisticsOutputModel(
            home_team_goals_over_under=self.parse_over_under(goals.get("home")),
            away_team_goals_over_under=self.parse_over_under(goals.get("away")),
            total_goals_over_under=self.parse_over_under(raw.get("under_over")),
            suggested_advice=raw.get("advice"),
            suggested_team_winner=suggested_winner,
            suggested_team_winner_comment=winner_info.get("comment"),
            home_team_win_probability=self.parse_percent(percent.get("home")),
            draw_probability=self.parse_percent(percent.get("draw")),
            away_team_win_probability=self.parse_percent(percent.get("away")),
        )

    def parse_over_under(self, s: str | None) -> float | None:
        if not s:
            return None
        # strip leading "+" if present
        return float(s.replace("+", ""))

    def parse_percent(self, s: str | None) -> float | None:
        if not s or not s.endswith("%"):
            return None
        return float(s[:-1])

    def get_standings(self) -> tuple[TeamStandingOutputModel | None, TeamStandingOutputModel | None]:
        """
        Get the standings for the home and away teams in the match.

        Returns:
            tuple: A tuple containing the standings for the home team and away team.
        """
        home_team_standing = TeamStanding.objects.filter(
            league_team__team=self.sport_match.home_team,
            league_team__league=self.sport_match.league,
        ).first()
        away_team_standing = TeamStanding.objects.filter(
            league_team__team=self.sport_match.away_team,
            league_team__league=self.sport_match.league,
        ).first()

        return (
            TeamStandingOutputModel.from_django(home_team_standing) if home_team_standing else None,
            TeamStandingOutputModel.from_django(away_team_standing) if away_team_standing else None
        )
