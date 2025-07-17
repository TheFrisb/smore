import logging
from datetime import datetime, timedelta

from core.services.api.league_service import LeagueService
from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService

logger = logging.getLogger(__name__)


def update_scores():
    football_api_service = FootballApiService()
    basketball_api_service = BasketballApiService()

    start_date = datetime.today()

    football_api_service.populate_matches(start_date, start_date)
    basketball_api_service.populate_matches(start_date, start_date)


def load_matches():
    start_time = datetime.today() - timedelta(days=1)
    end_time = datetime.today() + timedelta(days=6)

    football_api_service = FootballApiService()
    basketball_api_service = BasketballApiService()

    football_api_service.populate_matches(start_time, end_time)
    # basketball_api_service.populate_matches(start_time, end_time)


def update_league_season_year():
    league_service = LeagueService()
    league_service.update_league_season_year()
