from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


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
    league: SportLeagueOutputModel = Field(..., description="The league the team belongs to")

    model_config = ConfigDict(
        from_attributes=True
    )


class SportMatchOutputModel(BaseModel):
    external_id: int = Field(..., description="The external ID of the match")
    home_team: SportTeamOutputModel = Field(..., description="The home team in the match")
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

    model_config = ConfigDict(
        from_attributes=True
    )
