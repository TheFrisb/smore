from __future__ import annotations

import logging
from datetime import timedelta, datetime
from typing import Optional, List, Union

from django.db.models import QuerySet, Q
from django.utils import timezone
from langchain_core.tools import tool
from pydantic import BaseModel, Field, ConfigDict

from ai_assistant.v2.service.MatchInsightBuilder import MatchInsightBuilder
from ai_assistant.v2.types import SportLeagueOutputModel, SportMatchOutputModel, SportMatchInsightOutputModel
from core.models import SportMatch
from core.services.football_api_service import allowed_league_ids

logger = logging.getLogger(__name__)


class GetMatchesByLeagueInput(BaseModel):
    league: SportLeagueOutputModel = Field(..., description="The league for which to fetch matches")
    kickoff_datetime: Union[None, datetime] = Field(
        None,
        description="Optional kick-off datetime to filter matches (matches on the same day as this datetime)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True and datetime is not provided, only return matches in the future relative to the current time"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class GetMatchesByTeamInput(BaseModel):
    external_team_id: int = Field(..., description="The external ID of the team for which to fetch matches")
    kickoff_datetime: Union[None, datetime] = Field(
        None,
        description="Optional kick-off datetime to filter matches (matches on the same day as this datetime)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True and datetime is not provided, only return matches in the future relative to the current time"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


class GetMatchesByTeamList(BaseModel):
    external_team_ids: List[int] = Field(..., description="List of external team IDs for which to fetch matches")
    kickoff_datetime: Union[None, datetime] = Field(
        None,
        description="Optional kick-off datetime to filter matches (matches on the same day as this datetime)"
    )
    upcoming_only: Optional[bool] = Field(
        False,
        description="If True and datetime is not provided, only return matches in the future relative to the current time"
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
    kickoff_datetime: Union[None, datetime] = Field(
        None,
        description="Optional kick-off datetime to filter matches (matches on the same day as this datetime)"
    )
    future_only: Optional[bool] = Field(
        False,
        description="If True and datetime is not provided, only return matches in the future relative to the current time"
    )
    number_of_matches: Optional[int] = Field(
        10,
        description="Number of random matches to return, default is 10"
    )

    model_config = ConfigDict(
        from_attributes=True
    )


@tool
def get_random_matches(random_match_input: RandomMatchInput) -> List[SportMatchOutputModel]:
    """
    Fetches random matches with available betting stats, optionally filtered by a datetime or future-only matches.

    Args:
        random_match_input (RandomMatchInput): Input containing optional datetime, future_only flag, and number of matches to return.

    Returns:
        List[SportMatchOutputModel]: A list containing a single random match, filtered by the provided criteria.
    """
    query_datetime = random_match_input.kickoff_datetime
    future_only = random_match_input.future_only

    logger.info(f"Fetching a random match with query datetime: {query_datetime}, future_only: {future_only}")

    query = SportMatch.objects.select_related('league__country', 'home_team', 'away_team')

    query = _add_date_filters_if_needed(query, query_datetime, future_only)

    matches = list(
        query.filter(league__external_id__in=allowed_league_ids).exclude(metadata={}).order_by("kickoff_datetime")[
        :random_match_input.number_of_matches
        ])
    if not matches:
        logger.warning("No matches found for the given criteria.")
        return []

    logger.info(
        f"Found {len(matches)} random matches with query datetime: {query_datetime}, future_only: {future_only}")
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
    query_datetime = league_input.kickoff_datetime
    future_only = league_input.upcoming_only

    logger.info(
        f"Fetching matches for league: {league.name} (ID: {league.external_id}) and query datetime: {query_datetime}, future_only: {future_only}")

    # Start building the query
    query = SportMatch.objects.filter(league__external_id=league.external_id).select_related(
        'league__country', 'home_team', 'away_team'
    )

    query = _add_date_filters_if_needed(query, query_datetime, future_only)

    matches = query.all().order_by('kickoff_datetime')

    logger.info(
        f"Found {len(matches)} matches for league: {league.name} (ID: {league.external_id}), and query datetime: {query_datetime}, future_only: {future_only}")
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
    query_datetime = team_input.kickoff_datetime
    future_only = team_input.upcoming_only

    logger.info(
        f"Fetching matches for team ID: {external_team_id} and query datetime: {query_datetime}, future_only: {future_only}")

    query = SportMatch.objects.filter(
        Q(home_team__external_id=external_team_id) | Q(away_team__external_id=external_team_id)).select_related(
        'league__country', 'home_team', 'away_team'
    )

    query = _add_date_filters_if_needed(query, query_datetime, future_only)

    matches = query.all().order_by('kickoff_datetime')

    logger.info(
        f"Found {len(matches)} matches for team ID: {external_team_id}, and query datetime: {query_datetime}, future_only: {future_only}")
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
    query_datetime = team_list_input.kickoff_datetime
    future_only = team_list_input.upcoming_only

    logger.info(
        f"Fetching matches for team IDs: {external_team_ids} and query datetime: {query_datetime}, future_only: {future_only}")

    query = SportMatch.objects.filter(
        Q(home_team__external_id__in=external_team_ids) | Q(away_team__external_id__in=external_team_ids)
    ).select_related('league__country', 'home_team', 'away_team')

    query = _add_date_filters_if_needed(query, query_datetime, future_only)

    matches = query.all().order_by('kickoff_datetime')

    logger.info(
        f"Found {len(matches)} matches for team IDs: {external_team_ids}, and query datetime: {query_datetime}, future_only: {future_only}")
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

    match = SportMatch.objects.filter(external_id=external_id).select_related(
        'league__country', 'home_team', 'away_team'
    ).first()

    logger.info(f"Found match with external ID: {external_id}")
    match_insight_builder = MatchInsightBuilder(match)
    return match_insight_builder.build_insight()


def _add_date_filters_if_needed(queryset: QuerySet,
                                kickoff_datetime: Optional[datetime],
                                future_only: bool) -> QuerySet:
    """    Adds date filters to the queryset based on the provided kickoff_datetime and future_only flag.
    Args:
        queryset (QuerySet): The initial queryset to filter.
        kickoff_datetime (Optional[datetime]): The datetime to filter matches by.
        future_only (bool): If True, only return matches in the future relative to the current time.
    Returns:
        QuerySet: The filtered queryset.
    """

    if kickoff_datetime:
        if not timezone.is_aware(kickoff_datetime):
            kickoff_datetime = timezone.make_aware(kickoff_datetime)

        start_of_day = kickoff_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        queryset = queryset.filter(kickoff_datetime__gte=start_of_day, kickoff_datetime__lt=end_of_day)
    elif future_only:
        queryset = queryset.filter(kickoff_datetime__gt=timezone.now())

    return queryset
