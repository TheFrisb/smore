from __future__ import annotations

import logging
from datetime import date
from typing import Optional, List, Union

from django.db.models import QuerySet, Q
from langchain_core.tools import tool
from pydantic import BaseModel, Field, ConfigDict

from ai_assistant.v2.service.MatchInsightBuilder import MatchInsightBuilder
from ai_assistant.v2.types import SportLeagueOutputModel, SportMatchOutputModel, SportMatchInsightOutputModel
from core.models import SportMatch, ApiSportModel
from core.services.football_api_service import allowed_league_ids

logger = logging.getLogger(__name__)


class GetMatchesByLeagueInput(BaseModel):
    league: SportLeagueOutputModel = Field(..., description="The league for which to fetch matches")
    kickoff_date: Union[None, date] = Field(
        None,
        description="Optional kick-off date to filter matches (matches on the same day as this date)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True, only matches that are not finished will be returned (i.e., matches in the future relative to the current time)"
    )
    number_of_matches: Optional[int] = Field(
        10,
        description="Number of matches to return, default is 10"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class GetMatchesByTeamInput(BaseModel):
    external_team_id: int = Field(..., description="The external ID of the team for which to fetch matches")
    kickoff_date: Union[None, date] = Field(
        None,
        description="Optional kick-off date to filter matches (matches on the same day as this date)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True, only matches that are not finished will be returned (i.e., matches in the future relative to the current time)"
    )
    number_of_matches: Optional[int] = Field(
        10,
        description="Number of matches to return, default is 10"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class GetMatchesByTeamList(BaseModel):
    external_team_ids: List[int] = Field(..., description="List of external team IDs for which to fetch matches")
    kickoff_date: Union[None, date] = Field(
        None,
        description="Optional kick-off date to filter matches (matches on the same day as this date)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True, only matches that are not finished will be returned (i.e., matches in the future relative to the current time)"
    )
    number_of_matches: Optional[int] = Field(
        30,
        description="Number of random matches to return, default is 30"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class GetMatchByExternalIdInput(BaseModel):
    external_id: int = Field(..., description="The external ID of the match to fetch")

    model_config = ConfigDict(
        from_attributes=True
    )


class RandomMatchInput(BaseModel):
    kickoff_date: Union[None, date] = Field(
        None,
        description="Optional kick-off date to filter matches (matches on the same day as this date)"
    )
    future_only: Optional[bool] = Field(
        False,
        description="If True, only matches that are not finished will be returned (i.e., matches in the future relative to the current time)"
    )
    number_of_matches: Optional[int] = Field(
        20,
        description="Number of random matches to return, default is 20"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class HeadToHeadInput(BaseModel):
    home_team_external_id: int = Field(..., description="External ID of the home team")
    away_team_external_id: int = Field(..., description="External ID of the away team")
    kickoff_date: Union[None, date] = Field(
        None,
        description="Optional kick-off date to filter matches (matches on the same day as this date)"
    )
    future_only: Optional[bool] = Field(
        False,
        description="If True, only matches that are not finished will be returned (i.e., matches in the future relative to the current time)"
    )
    number_of_matches: Optional[int] = Field(
        30,
        description="Number of matches to return, default is 30"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


@tool
def get_head_to_head_matches(head_to_head_input: HeadToHeadInput) -> List[SportMatchOutputModel]:
    """
    Fetches head-to-head matches between two teams, optionally filtered by a datetime or future-only matches.

    Args:
        head_to_head_input (HeadToHeadInput): Input containing home team ID, away team ID, optional datetime.

    Returns:
        List[SportMatchOutputModel]: A list of head-to-head matches between the specified teams, filtered by the provided criteria.
    """
    home_team_id = head_to_head_input.home_team_external_id
    away_team_id = head_to_head_input.away_team_external_id
    query_date = head_to_head_input.kickoff_date

    logger.info(
        f"Fetching head-to-head matches for home team ID: {home_team_id} and away team ID: {away_team_id}, "
        f"query date: {query_date}")

    query = SportMatch.objects.filter(
        Q(home_team__external_id=home_team_id, away_team__external_id=away_team_id) |
        Q(home_team__external_id=away_team_id, away_team__external_id=home_team_id),
        type=ApiSportModel.SportType.SOCCER
    ).select_related('league__country', 'home_team', 'away_team')

    query = _add_date_filters_if_needed(query, query_date, future_only=head_to_head_input.future_only)

    matches = query.all().order_by('kickoff_datetime')[:head_to_head_input.number_of_matches]

    logger.info(f"Found {len(matches)} head-to-head matches for teams with IDs: {home_team_id} and {away_team_id}")
    return [SportMatchOutputModel.model_validate(match) for match in matches]


@tool
def get_random_matches(random_match_input: RandomMatchInput) -> List[SportMatchOutputModel]:
    """
    Fetches random matches with available betting stats, optionally filtered by a datetime or future-only matches.

    Args:
        random_match_input (RandomMatchInput): Input containing optional datetime, future_only flag, and number of matches to return.

    Returns:
        List[SportMatchOutputModel]: A list containing a single random match, filtered by the provided criteria.
    """
    query_date = random_match_input.kickoff_date
    future_only = random_match_input.future_only

    logger.info(f"Fetching a random match with query date: {query_date}, future_only: {future_only}")

    query = SportMatch.objects.select_related('league__country', 'home_team', 'away_team')

    query = _add_date_filters_if_needed(query, query_date, future_only)

    matches = list(
        query.filter(league__external_id__in=allowed_league_ids, type=ApiSportModel.SportType.SOCCER).exclude(
            metadata={}).order_by("kickoff_datetime")[
        :random_match_input.number_of_matches
        ])
    if not matches:
        logger.warning("No matches found for the external IDs in allowed_league_ids")
        new_qs = SportMatch.objects.select_related('league__country', 'home_team', 'away_team')
        new_qs = _add_date_filters_if_needed(new_qs, query_date, future_only)
        matches = list(
            new_qs.filter(type=ApiSportModel.SportType.SOCCER).exclude(metadata={}).order_by("kickoff_datetime")[
            :random_match_input.number_of_matches
            ])

    logger.info(
        f"Found {len(matches)} random matches with query date: {query_date}, future_only: {future_only}")
    return [SportMatchOutputModel.model_validate(match) for match in matches]


@tool
def get_matches_by_league(league_input: GetMatchesByLeagueInput) -> List[SportMatchOutputModel]:
    """
    Fetches matches for a given league, optionally filtered by a datetime or upcoming matches.

    Args:
        league_input (GetMatchesByLeagueInput): Input containing the league, optional datetime, and future_only flag.

    Returns:
        List[SportMatchOutputModel]: A list of matches in the specified league, filtered by the provided criteria.
    """
    league = league_input.league
    query_date = league_input.kickoff_date
    future_only = league_input.upcoming_only

    logger.info(
        f"Fetching matches for league: {league.name} (ID: {league.external_id}) and query date: {query_date}, future_only: {future_only}")

    # Start building the query
    query = SportMatch.objects.filter(league__external_id=league.external_id,
                                      type=ApiSportModel.SportType.SOCCER).select_related(
        'league__country', 'home_team', 'away_team'
    )

    query = _add_date_filters_if_needed(query, query_date, future_only)

    matches = query.all().order_by('kickoff_datetime')[:league_input.number_of_matches]

    logger.info(
        f"Found {len(matches)} matches for league: {league.name} (ID: {league.external_id}), and query date: {query_date}, future_only: {future_only}")
    return [SportMatchOutputModel.model_validate(match) for match in matches]


@tool
def get_matches_by_team(team_input: GetMatchesByTeamInput) -> List[SportMatchOutputModel]:
    """
    Fetches matches for a given team, optionally filtered by a datetime or future-only matches.

    Args:
        team_input (GetMatchesByTeamInput): Input containing the external team ID, optional datetime, and upcoming_only flag.

    Returns:
        List[SportMatchOutputModel]: A list of matches involving the specified team, filtered by the provided criteria.
    """
    external_team_id = team_input.external_team_id
    query_date = team_input.kickoff_date
    future_only = team_input.upcoming_only

    logger.info(
        f"Fetching matches for team ID: {external_team_id} and query date: {query_date}, future_only: {future_only}")

    query = SportMatch.objects.filter(
        Q(home_team__external_id=external_team_id) | Q(away_team__external_id=external_team_id),
        type=ApiSportModel.SportType.SOCCER).select_related(
        'league__country', 'home_team', 'away_team'
    )

    query = _add_date_filters_if_needed(query, query_date, future_only)

    matches = query.all().order_by('kickoff_datetime')[:team_input.number_of_matches]

    logger.info(
        f"Found {len(matches)} matches for team ID: {external_team_id}, and query date: {query_date}, future_only: {future_only}")
    return [SportMatchOutputModel.model_validate(match) for match in matches]


@tool
def get_matches_by_team_list(team_list_input: GetMatchesByTeamList) -> List[SportMatchOutputModel]:
    """
    Fetches matches for a list of teams, optionally filtered by a datetime or future-only matches.

    Args:
        team_list_input (GetMatchesByTeamList): Input containing the list of external team IDs, optional datetime, and upcoming_only flag.

    Returns:
        List[SportMatchOutputModel]: A list of matches involving the specified teams, filtered by the provided criteria.
    """
    external_team_ids = team_list_input.external_team_ids
    query_date = team_list_input.kickoff_date
    future_only = team_list_input.upcoming_only

    logger.info(
        f"Fetching matches for team IDs: {external_team_ids} and query date: {query_date}, future_only: {future_only}")

    query = SportMatch.objects.filter(
        Q(home_team__external_id__in=external_team_ids) | Q(away_team__external_id__in=external_team_ids),
        type=ApiSportModel.SportType.SOCCER
    ).select_related('league__country', 'home_team', 'away_team')

    query = _add_date_filters_if_needed(query, query_date, future_only)

    matches = query.all().order_by('kickoff_datetime')[:team_list_input.number_of_matches]

    logger.info(
        f"Found {len(matches)} matches for team IDs: {external_team_ids}, and query date: {query_date}, future_only: {future_only}")
    return [SportMatchOutputModel.model_validate(match) for match in matches]


@tool
def get_match_insights_by_external_id(match_input: GetMatchByExternalIdInput) -> SportMatchInsightOutputModel:
    """
    Fetches match insights for a given match by its external ID.

    Args:
        match_input (GetMatchByExternalIdInput): Input containing the external ID of the match.

    Returns:
        SportMatchOutputModel: The match details for the specified external ID.
    """
    external_id = match_input.external_id

    logger.info(f"Fetching match insights for external ID: {external_id}")

    match = SportMatch.objects.filter(external_id=external_id, type=ApiSportModel.SportType.SOCCER).select_related(
        'league__country', 'home_team', 'away_team'
    ).first()

    logger.info(f"Found match with external ID: {external_id}")
    match_insight_builder = MatchInsightBuilder(match)
    return match_insight_builder.build_insight()


def _add_date_filters_if_needed(queryset: QuerySet,
                                kickoff_date: Optional[date],
                                future_only: bool) -> QuerySet:
    """    Adds date filters to the queryset based on the provided kickoff_datetime and future_only flag.
    Args:
        queryset (QuerySet): The initial queryset to filter.
        kickoff_date (Optional[date]): Optional date to filter matches that occur on the same day.
        future_only (bool): If True, only return upcoming matches that are not yet finished.
    Returns:
        QuerySet: The filtered queryset.
    """

    if kickoff_date:
        logger.info(f"Filtering matches for kickoff date: {kickoff_date}")
        queryset = queryset.filter(kickoff_datetime__date=kickoff_date)
    elif future_only:
        queryset = queryset.filter(status__in=[
            SportMatch.Status.SCHEDULED,
            SportMatch.Status.IN_PROGRESS
        ])

    return queryset
