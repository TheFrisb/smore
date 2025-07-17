from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from core.models import TeamStanding


class SportCountryOutputModel(BaseModel):
    name: str = Field(..., max_length=255, description="The name of the country")
    code: Optional[str] = Field(None, max_length=255, description="The country code (optional)")

    model_config = ConfigDict(
        from_attributes=True
    )


class SportLeagueOutputModel(BaseModel):
    external_id: int = Field(..., description="The external ID of the league")
    name: str = Field(..., max_length=255, description="The name of the league")
    country: SportCountryOutputModel = Field(..., description="The country associated with the league")

    model_config = ConfigDict(
        from_attributes=True
    )


class SportTeamOutputModel(BaseModel):
    external_id: int = Field(..., description="The external ID of the team")
    name: str = Field(..., max_length=255, description="The name of the team")
    leagues: Optional[list[SportLeagueOutputModel]] = Field(
        None,
        description="List of leagues the team is associated with, if available",
        alias="leagues_list"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class SportMatchOutputModel(BaseModel):
    external_id: int = Field(..., description="The external ID of the match")
    home_team: SportTeamOutputModel = Field(..., description="The home team in the match")
    home_team_score: Optional[str] = Field(
        None,
        description="The score of the home team in the match, if available"
    )
    away_team_score: Optional[str] = Field(
        None,
        description="The score of the away team in the match, if available"
    )
    away_team: SportTeamOutputModel = Field(..., description="The away team in the match")
    league: SportLeagueOutputModel = Field(..., description="The league the match belongs to")
    kickoff_datetime: datetime = Field(..., description="The date and time of the match kickoff")

    model_config = ConfigDict(
        from_attributes=True
    )


class PredictionStatisticsOutputModel(BaseModel):
    home_team_goals_over_under: Optional[float] = Field(
        None,
        description="Prediction statistic for whether the home team will score more or less than a certain number of goals, e.g. -2.5 means the home team is predicted to score less than 2.5 goals (under 2.5 goals) and +2.5 means the home team is predicted to score more than 2.5 goals (over 2.5 goals)"
    )
    away_team_goals_over_under: Optional[float] = Field(
        None,
        description="Prediction statistic for whether the away team will score more or less than a certain number of goals, e.g. -2.5 means the away team is predicted to score less than 2.5 goals (under 2.5 goals) and +2.5 means the away team is predicted to score more than 2.5 goals (over 2.5 goals)"
    )
    total_goals_over_under: Optional[float] = Field(
        None,
        description="Prediction statistic for the total number of goals scored in the match, e.g. -2.5 means the total goals are predicted to be less than 2.5 (under 2.5 goals) and +2.5 means the total goals are predicted to be more than 2.5 (over 2.5 goals)"
    )
    suggested_advice: Optional[str] = Field(
        None,
        max_length=1000,
        description="Suggested betting advice based on the prediction statistics, e.g. 'Double chance : Real Madrid or draw'"
    )
    suggested_team_winner: Optional[SportTeamOutputModel] = Field(
        None,
        description="The team predicted to win the match, if applicable"
    )
    suggested_team_winner_comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Betting advice comment for the suggested team winner, e.g. 'Win or draw'"
    )
    home_team_win_probability: Optional[float] = Field(
        None,
        description="Probability of the home team winning the match, expressed as a percentage, e.g. '75' means 75% predicted probability of the home team winning"
    )
    away_team_win_probability: Optional[float] = Field(
        None,
        description="Probability of the away team winning the match, expressed as a percentage, e.g. '10' means 10% predicted probability of the away team winning"
    )
    draw_probability: Optional[float] = Field(
        None,
        description="Probability of the match ending in a draw, expressed as a percentage, e.g. '15' means 15% predicted probability of a draw"
    )


class SportMatchInsightOutputModel(BaseModel):
    match: SportMatchOutputModel = Field(..., description="The match for which the insight is provided")
    home_team_history: Optional[list[SportMatchOutputModel]] = Field(
        None,
        description="Recent history of the home team, represented as a list of matches"
    )
    away_team_history: Optional[list[SportMatchOutputModel]] = Field(
        None,
        description="Recent history of the away team, represented as a list of matches"
    )

    home_team_upcoming_matches: Optional[list[SportMatchOutputModel]] = Field(
        None,
        description="Upcoming matches for the home team, represented as a list of matches"
    )
    away_team_upcoming_matches: Optional[list[SportMatchOutputModel]] = Field(
        None,
        description="Upcoming matches for the away team, represented as a list of matches"
    )

    head_to_head_matches: Optional[list[SportMatchOutputModel]] = Field(
        None,
        description="Recent head-to-head matches between the two teams, represented as a list of matches"
    )
    prediction_statistics: Optional[PredictionStatisticsOutputModel] = Field(
        None,
        description="Prediction statistics for the match, if available"
    )
    home_team_standings: Optional["TeamStandingOutputModel"] = Field(
        None,
        description="Standings and performance statistics for the home team, if available"
    )
    away_team_standings: Optional["TeamStandingOutputModel"] = Field(
        None,
        description="Standings and performance statistics for the away team, if available"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class PlayerOutputModel(BaseModel):
    external_id: int = Field(..., description="The external ID of the player")
    full_name: str = Field(..., max_length=255, description="The full name of the player")
    first_name: Optional[str] = Field(None, description="The first name of the player, if available")
    last_name: Optional[str] = Field(
        None, description="The last name of the player, if available"
    )
    age: Optional[int] = Field(
        None, description="The age of the player, if available"
    )
    birth_date: Optional[str] = Field(None, description="The birth date of the player, if available")
    birth_place: Optional[str] = Field(None, description="The birth place of the player, if available")
    birth_country: Optional[str] = Field(None, description="The birth country, if available")
    nationality: Optional[str] = Field(None, description="The nationality of the player, if available")
    height: Optional[str] = Field(
        None, description="The height of the player in centimeters, if available"
    )
    weight: Optional[str] = Field(
        None, description="The weight of the player in kilograms, if available"
    )
    position: Optional[str] = Field(
        None, description="The position of the player, if available"
    )
    number: Optional[str] = Field(
        None, description="The jersey number of the player, if available"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    )

    @classmethod
    def from_django(cls, player) -> "PlayerOutputModel":
        """
        Construct a PlayerOutputModel by manually building a dict from a Django Player instance.
        """
        player_data = {
            "external_id": player.external_id,
            "full_name": player.full_name,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "age": player.age,
            "birth_date": player.birth_date.isoformat() if player.birth_date else None,
            "birth_place": player.birth_place,
            "birth_country": player.birth_country,
            "nationality": player.nationality,
            "height": player.height,
            "weight": player.weight,
            "position": player.position,
            "number": player.number,
        }
        return cls.model_validate(player_data)


class TeamStandingOutputModel(BaseModel):
    season_year: int = Field(
        ...,
        description="The year of the season for which the standings are provided."
    )
    league_rank: int = Field(
        ...,
        description="The rank of the team in the league standings."
    )
    team: "SportTeamOutputModel" = Field(
        ...,
        description="Details of the team in the standings."
    )
    points: int = Field(
        ...,
        description="Total points accumulated by the team in the league standings."
    )
    league: "SportLeagueOutputModel" = Field(
        ...,
        description="Details of the league in which the team is standing."
    )
    # goals diff
    form: Optional[str] = Field(
        ...,
        description="The form of the team, represented as a string of results (e.g., 'WLDWW', W - Win, L - Loss, D - Draw), if games were played."
    )
    total_games_played: int = Field(
        ...,
        description="Total number of games played by the team in the league."
    )
    total_games_won: int = Field(
        ...,
        description="Total number of games won by the team in the league."
    )
    total_games_drawn: int = Field(
        ...,
        description="Total number of games drawn by the team in the league."
    )
    total_games_lost: int = Field(
        ...,
        description="Total number of games lost by the team in the league."
    )
    total_goals_scored: int = Field(
        ...,
        description="Total number of goals scored by the team in the league."
    )
    total_goals_conceded: int = Field(
        ...,
        description="Total number of goals conceded by the team in the league."
    )
    home_games_played: int = Field(
        ...,
        description="Total number of home games played by the team in the league."
    )
    home_games_won: int = Field(
        ...,
        description="Total number of home games won by the team in the league."
    )
    home_games_drawn: int = Field(
        ...,
        description="Total number of home games drawn by the team in the league."
    )
    home_games_lost: int = Field(
        ...,
        description="Total number of home games lost by the team in the league."
    )
    away_games_played: int = Field(
        ...,
        description="Total number of away games played by the team in the league."
    )
    away_games_won: int = Field(
        ...,
        description="Total number of away games won by the team in the league."
    )
    away_games_drawn: int = Field(
        ...,
        description="Total number of away games drawn by the team in the league."
    )
    home_goals_scored: int = Field(
        ...,
        description="Total number of goals scored by the team in home games."
    )
    away_goals_scored: int = Field(
        ...,
        description="Total number of goals scored by the team in away games."
    )
    home_goals_conceded: int = Field(
        ...,
        description="Total number of goals conceded by the team in home games."
    )
    away_goals_conceded: int = Field(
        ...,
        description="Total number of goals conceded by the team in away games."
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    )

    @classmethod
    def from_django(cls, team_standing: TeamStanding) -> "TeamStandingOutputModel":
        """
        Converts a Django TeamStanding instance to a TeamStandingOutputModel.
        """

        data = {
            "league": SportLeagueOutputModel.model_validate(team_standing.league_team.league),
            "team": SportTeamOutputModel.model_validate(team_standing.league_team.team),
            "season_year": team_standing.league_team.season,
            "league_rank": team_standing.data.get("rank", 0),
            "points": team_standing.data.get("points", 0),
            "form": team_standing.data.get("form"),
            "total_games_played": team_standing.data.get("all").get("played"),
            "total_games_won": team_standing.data.get("all").get("win"),
            "total_games_drawn": team_standing.data.get("all").get("draw"),
            "total_games_lost": team_standing.data.get("all").get("lose"),
            "total_goals_scored": team_standing.data.get("all").get("goals").get("for"),
            "total_goals_conceded": team_standing.data.get("all").get("goals").get("against"),
            "home_games_played": team_standing.data.get("home").get("played"),
            "home_games_won": team_standing.data.get("home").get("win"),
            "home_games_drawn": team_standing.data.get("home").get("draw"),
            "home_games_lost": team_standing.data.get("home").get("lose"),
            "away_games_played": team_standing.data.get("away").get("played"),
            "away_games_won": team_standing.data.get("away").get("win"),
            "away_games_drawn": team_standing.data.get("away").get("draw"),
            "home_goals_scored": team_standing.data.get("home").get("goals").get("for"),
            "away_goals_scored": team_standing.data.get("away").get("goals").get("for"),
            "home_goals_conceded": team_standing.data.get("home").get("goals").get("against"),
            "away_goals_conceded": team_standing.data.get("away").get("goals").get("against"),
        }

        return cls.model_validate(data)
