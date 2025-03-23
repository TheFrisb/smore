from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        basketball_api_service = BasketballApiService()
        football_api_service = FootballApiService()

        start_date = datetime(2025, 3, 9, tzinfo=timezone.utc)
        end_date = datetime(2025, 3, 29, tzinfo=timezone.utc)

        football_api_service.fetch_sport_matches(start_date, end_date)
        basketball_api_service.fetch_sport_matches(start_date, end_date)
