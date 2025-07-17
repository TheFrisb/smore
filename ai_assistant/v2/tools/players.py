from typing import Optional

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ai_assistant.v2.types import PlayerOutputModel
from core.models import Player, ApiSportModel


class PlayerInput(BaseModel):
    name_query: Optional[str] = Field(None, description="Name or partial name of the player to search for.")
    external_id: Optional[int] = Field(
        None, description="External ID of the player to fetch specific player information."
    )


@tool
def get_player_info(player_input: PlayerInput) -> Optional[PlayerOutputModel]:
    """
    Fetches player information for a given player name or external ID.

    Args:
        player_input (PlayerInput): Input containing player name or external ID.

    Returns:
        dict: Player information if found, otherwise None.
    """
    player = None

    if player_input.external_id is not None:
        player = Player.objects.filter(external_id=player_input.external_id).first()

    if player is not None:
        return PlayerOutputModel.model_validate(player)

    if player_input.name_query:
        player = Player.objects.annotate(
            similarity=TrigramSimilarity(
                Lower(Unaccent("name")), Lower(Unaccent(Value(player_input.name_query)))
            )
        ).filter(similarity__gt=0.5, type=ApiSportModel.SportType.TEMP_FIX).order_by("-similarity").first()

    if player is not None:
        return PlayerOutputModel.model_validate(player)

    return None
