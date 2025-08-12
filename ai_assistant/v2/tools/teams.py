import logging

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ai_assistant.v2.types import SportTeamOutputModel, SportLeagueOutputModel
from core.models import SportTeam, ApiSportModel

logger = logging.getLogger(__name__)


class TeamInput(BaseModel):
    team_name: str = Field(
        description="The official name of the team, e.g., 'Manchester United' or 'Real Madrid' to look up.")


class TeamLeagueInput(BaseModel):
    league_external_id: int = Field(
        description="The external ID of the league to filter teams by, usually fetched from a tool like get_league_info."
    )


@tool
def get_team_info(team_input: TeamInput) -> SportTeamOutputModel:
    """
    Fetches information about a sports team based on the provided team name.

    Args:
        team_input (TeamInput): Input model containing the official full team name to search for.

    Returns:
        SportTeamOutputModel: The    output model containing the team's external ID, name, and league information.
    """

    query = team_input.team_name.lower().strip()
    logger.info(f"Searching for team with name: {query}")

    teams = (
        SportTeam.objects.annotate(
            similarity=TrigramSimilarity(
                Lower(Unaccent("name")), Lower(Unaccent(Value(query)))
            )
        )
        .prefetch_related("leagues")
        .filter(similarity__gt=0.5, type=ApiSportModel.SportType.SOCCER)
        .order_by("-similarity")
    )

    if teams.exists():
        team = teams.first()
        logger.info(f"Matched team name: {query} to {team.name}")
        return SportTeamOutputModel(
            external_id=team.external_id,
            name=team.name,
            leagues_list=[
                SportLeagueOutputModel.model_validate(league)
                for league in team.leagues_list
            ]
        )

    else:
        logger.warning(f"No team found for name: {query}")
        raise ValueError(f"No team found for name: {query}")


@tool
def get_team_infos_by_league(team_league_input: TeamLeagueInput) -> list[SportTeamOutputModel]:
    """
    Fetches all teams in a specific league based on the provided league external ID.

    Args:
        team_league_input (TeamLeagueInput): Input model containing the league's external ID to filter teams by.

    Returns: 
        list[SportTeamOutputModel]: A list of output models containing each team's information.
    """

    logger.info(f"Fetching teams for league with external ID: {team_league_input.league_external_id}")

    teams = (
        SportTeam.objects.filter(
            league__external_id=team_league_input.league_external_id,
            type=ApiSportModel.SportType.SOCCER,
            leagues__in=team_league_input.league_external_id
        )
        .prefetch_related("leagues")
        .order_by("name")
    )

    if teams.exists():
        return [SportTeamOutputModel.model_validate(team) for team in teams]

    else:
        logger.warning(f"No teams found for league with external ID: {team_league_input.league_external_id}")
        raise ValueError(f"No teams found for league with external ID: {team_league_input.league_external_id}")
