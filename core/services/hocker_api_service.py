import logging
from datetime import datetime, timezone

from core.models import ApiSportModel, Product, SportMatch
from core.services.sport_api_service import SportApiService

logger = logging.getLogger(__name__)


class HockeyApiService(SportApiService):

    def populate_matches(self, start_date: datetime, end_date: datetime) -> None:
        endpoint = f"{self._get_base_url(ApiSportModel.SportType.NHL)}/games"
        self.fetch_sport_matches(
            start_date,
            end_date,
            endpoint,
            ApiSportModel.SportType.NHL,
            self._process_fixture,
        )

    def _process_fixture(self, item):
        product_obj = Product.objects.get(name=Product.Names.NFL_NHL)

        external_id = item.get("id")
        kickoff_timestamp = item.get("timestamp")
        kickoff_datetime = datetime.fromtimestamp(kickoff_timestamp, tz=timezone.utc)
        league_id = item.get("league").get("id")

        home_team_score = item.get("scores").get("home")
        away_team_score = item.get("scores").get("away")

        if not home_team_score:
            home_team_score = ""
        if not away_team_score:
            away_team_score = ""

        logger.info(f"Processing match ID: {external_id} for league ID: {league_id}")
        league_obj = self._get_league_obj(league_id, ApiSportModel.SportType.NHL)

        if not league_obj:
            logger.error(
                f"League ID: {league_id} not found. Skipping processing for match ID: {external_id}"
            )
            return

        home_team_obj = self._create_or_update_team(
            item.get("teams").get("home"),
            league_obj,
            ApiSportModel.SportType.NHL,
            product_obj,
        )
        away_team_obj = self._create_or_update_team(
            item.get("teams").get("away"),
            league_obj,
            ApiSportModel.SportType.NHL,
            product_obj,
        )

        match_obj = SportMatch.objects.filter(
            external_id=external_id, type=ApiSportModel.SportType.NHL
        ).first()

        if match_obj:
            try:
                match_obj.home_team_score = home_team_score
                match_obj.away_team_score = away_team_score
                match_obj.kickoff_datetime = kickoff_datetime
                match_obj.save()
                logger.info(f"Updated NHL match: {match_obj}")
            except Exception as e:
                logger.error(f"Failed to update NHL match: {e}")
                return
        else:
            try:
                match_obj = SportMatch.objects.create(
                    external_id=external_id,
                    type=ApiSportModel.SportType.NHL,
                    league=league_obj,
                    home_team=home_team_obj,
                    away_team=away_team_obj,
                    home_team_score=home_team_score,
                    away_team_score=away_team_score,
                    kickoff_datetime=kickoff_datetime,
                    product=product_obj,
                )
                logger.info(f"Successfully created NHL match: {match_obj}")
            except Exception as e:
                logger.error(f"Failed to create NHL match: {e}")
