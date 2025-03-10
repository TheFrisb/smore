from django.core.management.base import BaseCommand

from core.models import SportLeague
from core.services.football_api_service import FootballApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        api_service = FootballApiService()

        for league in SportLeague.objects.all().values_list("external_id", flat=True):
            api_service.populate_matches_per_league_id(league)
