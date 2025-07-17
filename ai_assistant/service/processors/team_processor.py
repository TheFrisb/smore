import logging
from datetime import date
from typing import Optional

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower
from django.utils import timezone

from ai_assistant.service.data import PromptContext, PromptType
from ai_assistant.service.processors.base_processor import BaseProcessor
from core.models import SportTeam, SportMatch, ApiSportModel, SportLeague
from core.services.football_api_service import allowed_league_ids

logger = logging.getLogger(__name__)


class TeamProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="TeamProcessor", llm_model=None)

    def process(self, prompt_context: PromptContext):
        """
        Load the extracted team names into team objects.
        """
        logging.info(f" Processing team names: {prompt_context.team_names}")
        prompt_type = prompt_context.prompt_type

        matched_teams = []

        if prompt_context.team_names:
            logger.info(f"Found extracted team names: {prompt_context.team_names}")
            matched_teams.extend(
                self._find_extracted_team_names(prompt_context.team_names)
            )

        if prompt_context.leagues:
            logger.info(
                f"Fetching random teams for league-related prompt type: {prompt_type}"
            )
            filter_date = (
                None
                if not prompt_context.suggested_dates
                else prompt_context.suggested_dates[0]
            )
            matched_teams.extend(
                self._get_random_teams(
                    filter_date=filter_date,
                    filter_by_leagues=[
                        obj.external_id for obj in prompt_context.league_objs
                    ],
                    prompt_type=prompt_type,
                )
            )

        if (
                prompt_type in self.get_match_related_prompt_types()
                and not prompt_context.team_names
                and not prompt_context.leagues
        ):
            logger.info(
                f"No team names found in prompt context: {prompt_context}. Assuming that random teams are needed."
            )
            filter_date = (
                None
                if not prompt_context.suggested_dates
                else prompt_context.suggested_dates[0]
            )
            matched_teams.extend(
                self._get_random_teams(
                    filter_date=filter_date,
                    prompt_type=prompt_type,
                    filter_by_leagues=None,
                )
            )

        prompt_context.team_objs = matched_teams

    def _get_random_teams(
            self,
            filter_date: Optional[date],
            filter_by_leagues: Optional[list[SportLeague]],
            prompt_type: PromptType,
    ):
        """
        Fetch a random set of teams from the database.
        """

        base_queryset = (
            SportMatch.objects.filter(
                type=ApiSportModel.SportType.SOCCER,
                metadata__isnull=False,
            )
            .prefetch_related("home_team", "away_team")
            .order_by("kickoff_datetime")
        )

        if filter_by_leagues:
            logger.info(f"Filtering by leagues: {filter_by_leagues}")
            base_queryset = base_queryset.filter(
                leagues__external_id__in=filter_by_leagues
            )
        else:
            base_queryset = base_queryset.filter(
                league__external_id__in=allowed_league_ids
            )

        initial_queryset = base_queryset
        matched_teams = []

        if filter_date:
            logger.info(
                f"Filter date found: {filter_date}. Attempting to load teams for that date."
            )
            initial_queryset = initial_queryset.filter(
                kickoff_datetime__date=filter_date
            )[:8]
        else:
            initial_queryset = initial_queryset.filter(
                kickoff_datetime__date__gte=timezone.now()
            )[:8]

        if initial_queryset.exists():
            logger.info(
                f"Found {len(initial_queryset)} sport matches to fetch teams from."
            )
            matched_teams = self._extract_teams_from_matches(
                initial_queryset,
                prompt_type,
            )
        else:
            logger.info(f"No matches found for queryset: {initial_queryset}.")

        return matched_teams

    def _extract_teams_from_matches(
            self, matches: list[SportMatch], prompt_type: PromptType
    ):
        """
        Extract teams from the matches.
        """
        logger.info(f"Extracting teams from matches: {matches}")

        teams = set()
        for match in matches:
            if prompt_type == PromptType.SINGLE_MATCH_PREDICTION and len(teams) == 2:
                logger.info(
                    f"Already extracted 2 teams for prompt type: {prompt_type}. Breaking the loop."
                )
                break

            logger.info(
                f"Extracting teams from match: [{match.kickoff_datetime.strftime('%Y-%m-%d %H:%M')}] {match.home_team.name} vs {match.away_team.name}"
            )

            teams.add(match.home_team)
            teams.add(match.away_team)

            logger.info(
                f"Extracted teams: {match.home_team.name}, {match.away_team.name}"
            )

        loggable_team_string = ", ".join([team.name for team in teams])
        logger.info(f"Extracted teams: {loggable_team_string}")
        return list(teams)

    def _find_extracted_team_names(self, team_names: list[str]):
        if not team_names:
            raise ValueError("team_names cannot be empty")

        matched_teams = []

        logger.info(f"Finding teams: {team_names}")
        for team_name in team_names:
            team = self._find_team_by_name(team_name)
            if team:
                matched_teams.append(team)
            else:
                logger.warning(f" Team not found: {team_name}")

        if len(team_names) != len(matched_teams):
            logger.warning(
                f" Not all teams were found. Expected: {len(team_names)}, Found: {len(matched_teams)}"
            )

        return matched_teams

    def _find_team_by_name(self, team_name: str):
        """
        Attempt fuzzy matching using trigram similarity.
        """
        logger.info(f"Finding team: {team_name}")

        teams = (
            SportTeam.objects.annotate(
                similarity=TrigramSimilarity(
                    Lower(Unaccent("name")), Lower(Unaccent(Value(team_name)))
                )
            )
            .filter(similarity__gt=0.5, type=ApiSportModel.SportType.SOCCER)
            .order_by("-similarity")
        )

        logger.info(
            f" Returned {len(teams)} for team: {team_name}. Returned teams: {teams}"
        )

        if teams.exists():
            logger.info(f"Matched team name: {team_name} to {teams.first().name}")
            return teams.first()
        else:
            logger.warning(f" No team found for: {team_name}")
            return None
