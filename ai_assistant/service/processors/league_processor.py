import logging

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower

from ai_assistant.service.data import PromptContext
from ai_assistant.service.processors.base_processor import BaseProcessor
from core.models import SportLeague

logger = logging.getLogger(__name__)


class LeagueProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="LeagueProcessor", llm_model=None)

    def process(self, prompt_context: PromptContext):
        """
        Load the extracted league names into league objects.
        """
        logging.info(
            f"[{self.name}] Processing league names: {prompt_context.league_names}"
        )

        matched_leagues = []

        for league_names in prompt_context.league_names:
            league = self.find_league(league_names)
            if league:
                logger.info(f"[{self.name}] Found league: {league}")
                matched_leagues.append(league)
            else:
                logger.warning(f"[{self.name}] League not found: {league_names}")

        if len(prompt_context.league_names) != len(matched_leagues):
            logger.warning(
                f"[{self.name}] Not all leagues were found. Expected: {len(prompt_context.league_names)}, Found: {len(matched_leagues)}"
            )

        prompt_context.league_objs = matched_leagues

    def find_league(self, league_name: str):
        """
        Attempt fuzzy matching using trigram similarity.
        """
        logger.info(f"[{self.name}] Finding league: {league_name}")

        leagues = (
            SportLeague.objects.annotate(
                similarity=TrigramSimilarity(
                    Lower(Unaccent("name")), Lower(Unaccent(Value(league_name)))
                )
            )
            .filter(similarity__gt=0.5)
            .order_by("-similarity")
        )

        logger.info(
            f"[{self.name}] Returned {len(leagues)} for league: {league_name}. Returned leagues: {leagues}"
        )

        if leagues.exists():
            return leagues.first()
        else:
            logger.warning(f"[{self.name}] No league found for: {league_name}")
            return None
