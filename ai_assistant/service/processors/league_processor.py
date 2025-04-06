import logging

from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower

from ai_assistant.service.data import PromptContext
from ai_assistant.service.processors.base_processor import BaseProcessor
from core.models import SportLeague, SportCountry, ApiSportModel

logger = logging.getLogger(__name__)


class LeagueProcessor(BaseProcessor):
    def __init__(self):
        super().__init__(name="LeagueProcessor", llm_model=None)

    def process(self, prompt_context: PromptContext):
        """
        Load the extracted league names into league objects.
        """
        logging.info(f" Processing league names: {prompt_context.leagues}")

        matched_leagues = []

        for league_dict in prompt_context.leagues:
            league = self.find_league(league_dict.league_name, league_dict.country)
            if league:
                logger.info(f"Found league: {league}")
                matched_leagues.append(league)
            else:
                logger.warning(f" League not found: {league_dict}")

        if len(prompt_context.leagues) != len(matched_leagues):
            logger.warning(
                f" Not all leagues were found. Expected: {len(prompt_context.leagues)}, Found: {len(matched_leagues)}"
            )

        prompt_context.league_objs = matched_leagues

    def find_league(self, league_name: str, country_name):
        """
        Attempt fuzzy matching using trigram similarity.
        """
        logger.info(f"Finding league: {league_name}")
        country = None

        if country_name:
            country = (
                SportCountry.objects.annotate(
                    similarity=TrigramSimilarity(
                        Lower(Unaccent("name")), Lower(Unaccent(Value(country_name)))
                    )
                )
                .filter(similarity__gt=0.5)
                .first()
            )
            if country:
                logger.info(f"Found country: {country.name}")
            else:
                logger.warning(f" No country found for: {country_name}")

        leagues = SportLeague.objects.annotate(
            similarity=TrigramSimilarity(
                Lower(Unaccent("name")), Lower(Unaccent(Value(league_name)))
            )
        )

        if country:
            logger.info(f"Filtering league by country: {country}")
            leagues = leagues.filter(country=country)

        leagues.filter(
            similarity__gt=0.5, type=ApiSportModel.SportType.SOCCER
        ).order_by("-similarity")

        logger.info(
            f" Returned {len(leagues)} for league: {league_name}. Returned leagues: {leagues}"
        )

        if leagues.exists():
            return leagues.first()
        else:
            logger.warning(f" No league found for: {league_name}")
            return None
