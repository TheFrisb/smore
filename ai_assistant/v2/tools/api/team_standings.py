from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ai_assistant.v2.types import TeamStandingOutputModel
from core.models import TeamStanding


class TeamStandingInput(BaseModel):
    external_league_id: int = Field(
        ...,
        description="External ID of the league to fetch team standings for."
    )
    external_team_id: int = Field(
        ...,
        description="External ID of the team to fetch standings for."
    )
    season_year: int = Field(
        ...,
        description="Season year for which the standings are to be fetched."
    )


@tool
def get_team_standing(
        input_data: TeamStandingInput
) -> Optional[TeamStandingOutputModel]:
    """
    Fetches the current standing and performance statistics of a specific team external id in a given league external id for a specific season year.

    Args:
        input_data (TeamStandingInput): Input model containing the external league ID, external team ID, and season year.

    Returns:
        Optional[TeamStandingOutputModel]: A model containing the team's standing and performance statistics, or None if the team standing does not exist.
    """
    team_standing = TeamStanding.objects.filter(
        league_team__league__external_id=input_data.external_league_id,
        league_team__team__external_id=input_data.external_team_id,
    ).first()

    if not team_standing:
        return None

    return TeamStandingOutputModel.from_django(team_standing)


TeamStandingOutputModel.model_rebuild()
