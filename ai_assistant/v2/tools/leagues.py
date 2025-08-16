import logging

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ai_assistant.v2.types import SportLeagueOutputModel, SportCountryOutputModel
from core.models import ApiSportModel, SportLeague

logger = logging.getLogger(__name__)


class LeagueInput(BaseModel):
    league_name: str = Field(
        description="The official name of the league, e.g., 'Premier League' or 'La Liga' to look up."
    )


@tool
def get_league_info(league_input: LeagueInput) -> SportLeagueOutputModel:
    """
    Fetches information about a sports league based on the provided league name.

    Args:
        league_input (LeagueInput): Input model containing the official full league name to search for.

    Returns:
        SportLeagueOutputModel: The output model containing the league's information.
    """

    query = league_input.league_name.lower().strip()
    logger.info(f"Searching for league with name: {query}")

    leagues = (
        SportLeague.objects.annotate(
            similarity=TrigramSimilarity(
                Lower(Unaccent("name")), Lower(Unaccent(Value(query)))
            )
        )
        .prefetch_related("country")
        .filter(similarity__gt=0.5, type=ApiSportModel.SportType.SOCCER)
        .order_by("-similarity")
    )

    if leagues.exists():
        league = leagues.first()
        logger.info(f"Matched league name: {query} to {league.name}")
        return SportLeagueOutputModel(
            external_id=league.external_id,
            name=league.name,
            country=SportCountryOutputModel.model_validate(league.country),
        )

    else:
        logger.warning(f"No league found for name: {query}")
        raise ValueError(f"No league found for name: {query}")
