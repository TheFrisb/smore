from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ConfigDict

from ai_assistant.v2.types import SportTeamOutputModel, PlayerOutputModel
from core.models import SportMatch, ApiSportModel


class MatchInjuryInput(BaseModel):
    external_match_id: int = Field(
        ..., description="External ID of the match to fetch injury information for."
    )


class InjuryOutputModel(BaseModel):
    player: PlayerOutputModel = Field(
        ..., description="Details of the player who has sustained an injury."
    )
    injury_type: str = Field(..., description="Type of injury sustained by the player.")
    will_play_status: str = Field(
        ...,
        description="Status indicating whether the player will play in the match. E.g., 'Missing Fixture' means the play is not expected to play and 'Questionable' means the player is uncertain to play.",
    )

    model_config = ConfigDict(from_attributes=True)


class TeamWithInjuryOutputModel(BaseModel):
    team: SportTeamOutputModel = Field(
        ..., description="The team for which the injury information is provided."
    )
    injuries: list[InjuryOutputModel] = Field(
        ..., description="List of injuries for players in the team."
    )

    model_config = ConfigDict(from_attributes=True)


@tool
def get_match_injuries(
    match_injury_input: MatchInjuryInput,
) -> Optional[list[TeamWithInjuryOutputModel]]:
    """
    Fetches injury information for players in a specific match, including details about the player, type of injury, and their expected participation status.

    Args:
        match_injury_input (MatchInjuryInput): Input model containing the external match ID.

    Returns:
        Optional[list[TeamWithInjuryOutputModel]]: A list of teams with their respective injury details, or None if the match does not support injuries data.
    """
    sport_match = SportMatch.objects.filter(
        external_id=match_injury_input.external_match_id,
        type=ApiSportModel.SportType.SOCCER,
    ).first()
    if not sport_match:
        return None

    from core.services.api.injuries_service import InjuriesService

    injuries_service = InjuriesService()
    response_body = injuries_service.fetch_injuries_for_match(sport_match)

    return injuries_service.load_injuries_for_tool(sport_match, response_body)
