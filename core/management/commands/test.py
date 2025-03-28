from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from core.models import ApiSportModel, Product
from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService
from core.services.hocker_api_service import HockeyApiService
from core.services.sport_api_service import SportApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        sport_api_service = SportApiService()

        sport_api_service.populate_countries(ApiSportModel.SportType.SOCCER)
        sport_api_service.populate_countries(ApiSportModel.SportType.BASKETBALL)
        sport_api_service.populate_countries(ApiSportModel.SportType.NHL)

        sport_api_service.populate_leagues(
            ApiSportModel.SportType.SOCCER,
            Product.objects.get(name=Product.Names.SOCCER),
        )

        sport_api_service.populate_leagues(
            ApiSportModel.SportType.BASKETBALL,
            Product.objects.get(name=Product.Names.BASKETBALL),
        )

        sport_api_service.populate_leagues(
            ApiSportModel.SportType.NHL,
            Product.objects.get(name=Product.Names.NFL_NHL_NCAA),
        )

    def load_matches(self):
        start_date = datetime(2025, 3, 28, tzinfo=timezone.utc)
        end_date = datetime(2025, 31, 31, tzinfo=timezone.utc)

        basketball_api_service = BasketballApiService()
        hockey_api_service = HockeyApiService()
        football_api_service = FootballApiService()

        basketball_api_service.populate_matches(start_date, end_date)
        hockey_api_service.populate_matches(start_date, end_date)
