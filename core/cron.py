import logging
from datetime import datetime

from core.services.football_api_service import FootballApiService

logger = logging.getLogger(__name__)


def update_prediction_scores():
    logger.info(f"[CRON | {datetime.now()}] Updating prediction scores")
    football_api_service = FootballApiService()
    football_api_service.update_prediction_scores()
    logger.info(f"[CRON | {datetime.now()}] Finished updating prediction scores")
