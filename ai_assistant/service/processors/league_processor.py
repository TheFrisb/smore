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
                logger.info(
                    f"Found league (ID: {league.id} - External ID: {league.external_id}): {league}"
                )
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
        Attempt fuzzy matching using trigram similarity with proper query chaining.
        """
        logger.info(
            f"Attempting to match league: {league_name} with country: {country_name}"
        )
        country = None

        if country_name:
            country = (
                SportCountry.objects.annotate(
                    similarity=TrigramSimilarity(
                        Lower(Unaccent("name")), Lower(Unaccent(Value(country_name)))
                    )
                )
                .filter(similarity__gt=0.5)
                .order_by("-similarity")[:1]
                .first()
            )
            if country:
                logger.info(
                    f"Matched country: {country.name} (ID: {country.id}, Name: {country.name})"
                )
            else:
                logger.warning(f"No country match for: {country_name}")

        leagues = SportLeague.objects.annotate(
            similarity=TrigramSimilarity(
                Lower(Unaccent("name")), Lower(Unaccent(Value(league_name)))
            )
        ).filter(type=ApiSportModel.SportType.SOCCER)

        if country:
            logger.info(f"Filtering by country: {country.name}")
            leagues = leagues.filter(country=country)

        leagues = leagues.filter(similarity__gt=0.5).order_by("-similarity")[:5]

        logger.info(f"Leagues found: {[l.name for l in leagues]}")

        best_match = leagues.first()
        if best_match:
            logger.info(
                f"Best league match: {best_match.name} (Similarity: {best_match.similarity:.2f})"
            )
            return best_match

        logger.warning(f"No league found for: {league_name}")
        return None
