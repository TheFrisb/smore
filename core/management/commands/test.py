from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from core.models import SportMatch
from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        basketball_api_service = BasketballApiService()
        basketball_api_service.populate_countries()
        basketball_api_service.populate_leagues()
        basketball_api_service.populate_upcoming_matches()

        tomorrow = datetime.now() + timedelta(days=2)

        SportMatch.objects.filter(kickoff_datetime__gte=tomorrow).delete()

        football_api_service = FootballApiService()
        football_api_service.populate_upcoming_matches()
