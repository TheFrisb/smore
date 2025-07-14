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


class SportMatchInsightOutputModel(BaseModel):
    match: SportMatchOutputModel = Field(..., description="The match for which the insight is provided")
    home_team_insight: str = Field(..., max_length=1000, description="Insight about the home team")
    away_team_insight: str = Field(..., max_length=1000, description="Insight about the away team")
    head_to_head_insight: str = Field(..., max_length=1000, description="Insight about the head-to-head matchup")
    prediction_statistics: str = Field(..., max_length=1000, description="Statistics related to the match prediction")
    
    model_config = ConfigDict(
        from_attributes=True
    )
