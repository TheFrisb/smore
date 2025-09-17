import logging
from datetime import datetime, timedelta

from core.services.api.league_service import LeagueService
from core.services.basketball_api_service import BasketballApiService
from core.services.football_api_service import FootballApiService

logger = logging.getLogger("cron")


def update_scores():
    logger.info(f"Job: update_scores started at {datetime.now()}")
    football_api_service = FootballApiService()
    basketball_api_service = BasketballApiService()

    start_date = datetime.today()

    football_api_service.populate_matches(start_date, start_date)
    basketball_api_service.populate_matches(start_date, start_date)
    logger.info(f"Job: update_scores finished at {datetime.now()}")


def load_matches():
    logger.info(f"Job: load_matches started at {datetime.now()}")
    start_time = datetime.today() - timedelta(days=1)
    end_time = datetime.today() + timedelta(days=6)

    football_api_service = FootballApiService()
    basketball_api_service = BasketballApiService()

    football_api_service.populate_matches(start_time, end_time)
    basketball_api_service.populate_matches(start_time, end_time)
    logger.info(f"Job: load_matches finished at {datetime.now()}")


def update_league_season_year():
    logger.info(f"Job: update_league_season_year started at {datetime.now()}")
    league_service = LeagueService()
    league_service.update_league_season_year()
    logger.error(f"Job: update_league_season_year finished at {datetime.now()}")


def update_standings():
    logger.info(f"Job: update_standings started at {datetime.now()}")
    league_service = LeagueService()
    league_service.fetch_and_update_team_standings()
    logger.error(f"Job: update_standings finished at {datetime.now()}")
