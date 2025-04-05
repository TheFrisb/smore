import logging

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower

from ai_assistant.service.data import PromptContext
from ai_assistant.service.processors.base_processor import BaseProcessor
from core.models import SportTeam

logger = logging.getLogger(__name__)


class TeamProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="TeamProcessor", llm_model=None)

    def process(self, prompt_context: PromptContext):
        """
        Load the extracted team names into team objects.
        """
        logging.info(
            f"[{self.name}] Processing team names: {prompt_context.team_names}"
        )

        matched_teams = []

        for team_name in prompt_context.team_names:
            team = self.find_team(team_name)
            if team:
                matched_teams.append(team)
            else:
                logger.warning(f"[{self.name}] Team not found: {team_name}")

        if len(prompt_context.team_names) != len(matched_teams):
            logger.warning(
                f"[{self.name}] Not all teams were found. Expected: {len(prompt_context.team_names)}, Found: {len(matched_teams)}"
            )

        prompt_context.team_objs = matched_teams

    def find_team(self, team_name: str):
        """
        Attempt fuzzy matching using trigram similarity.
        """
        logger.info(f"[{self.name}] Finding team: {team_name}")

        teams = (
            SportTeam.objects.annotate(
                similarity=TrigramSimilarity(
                    Lower(Unaccent("name")), Lower(Unaccent(Value(team_name)))
                )
            )
            .filter(similarity__gt=0.5)
            .order_by("-similarity")
        )

        logger.info(
            f"[{self.name}] Returned {len(teams)} for team: {team_name}. Returned teams: {teams}"
        )

        if teams.exists():
            return teams.first()
        else:
            logger.warning(f"[{self.name}] No team found for: {team_name}")
            return None
