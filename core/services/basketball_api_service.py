import logging
from datetime import datetime, timezone

from core.models import Product, SportMatch, ApiSportModel
from core.services.sport_api_service import SportApiService

logger = logging.getLogger(__name__)

BASKETBALL_NCAA_LEAGUE_IDS = [116, 423]


class BasketballApiService(SportApiService):

    def populate_matches(self, start_date: datetime, end_date: datetime) -> None:
        endpoint = f"{self._get_base_url(ApiSportModel.SportType.BASKETBALL)}/games"
        self.fetch_sport_matches(
            start_date,
            end_date,
            endpoint,
            ApiSportModel.SportType.BASKETBALL,
            self._process_fixture,
        )

    def _process_fixture(self, item):

        external_id = item.get("id")
        kickoff_timestamp = item.get("timestamp")
        kickoff_datetime = datetime.fromtimestamp(kickoff_timestamp, tz=timezone.utc)
        league_id = item.get("league").get("id")

        home_team_score = item.get("scores").get("home").get("total")
        away_team_score = item.get("scores").get("away").get("total")

        if not home_team_score:
            home_team_score = ""
        if not away_team_score:
            away_team_score = ""

        logger.info(f"Processing match ID: {external_id} for league ID: {league_id}")
        league_obj = self._get_league_obj(league_id, ApiSportModel.SportType.BASKETBALL)

        if not league_obj:
            logger.error(
                f"League ID: {league_id} not found. Skipping processing for match ID: {external_id}"
            )
            return

        home_team_obj = self._create_or_update_team(
            item.get("teams").get("home"),
            league_obj,
            ApiSportModel.SportType.BASKETBALL,
            self._get_product(league_obj),
        )
        away_team_obj = self._create_or_update_team(
            item.get("teams").get("away"),
            league_obj,
            ApiSportModel.SportType.BASKETBALL,
            self._get_product(league_obj),
        )

        match_obj = SportMatch.objects.filter(
            external_id=external_id,
            type=ApiSportModel.SportType.BASKETBALL,
        ).first()

        if match_obj:
            try:
                match_obj.home_team_score = home_team_score
                match_obj.away_team_score = away_team_score
                match_obj.kickoff_datetime = kickoff_datetime
                match_obj.save()
                logger.info(f"Updated basketball match: {match_obj}")
            except Exception as e:
                logger.error(f"Failed to update basketball match: {e}")
                return
        else:
            try:
                match_obj = SportMatch.objects.create(
                    external_id=external_id,
                    type=ApiSportModel.SportType.BASKETBALL,
                    league=league_obj,
                    home_team=home_team_obj,
                    away_team=away_team_obj,
                    home_team_score=home_team_score,
                    away_team_score=away_team_score,
                    kickoff_datetime=kickoff_datetime,
                    product=self._get_product(league_obj),
                )
                logger.info(f"Successfully created basketball match: {match_obj}")
            except Exception as e:
                logger.error(f"Failed to create basketball match: {e}")

    def _get_product(self, league):
        # sd
        return Product.objects.get(name=Product.Names.BASKETBALL)
