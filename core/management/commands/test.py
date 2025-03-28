from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService
from core.services.hocker_api_service import HockeyApiService
from core.services.sport_api_service import SportApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        sport_api_service = SportApiService()
        self.load_matches()

    def load_matches(self):
        start_date = datetime(2025, 3, 28, tzinfo=timezone.utc)
        end_date = datetime(2025, 3, 31, tzinfo=timezone.utc)

        basketball_api_service = BasketballApiService()
        hockey_api_service = HockeyApiService()
        football_api_service = FootballApiService()

        basketball_api_service.populate_matches(start_date, end_date)
        hockey_api_service.populate_matches(start_date, end_date)
