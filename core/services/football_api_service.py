import logging
from datetime import datetime, timezone

import requests
from django.utils import timezone as django_timezone

from core.models import (
    ApiSportModel,
    SportLeague,
    SportMatch,
)
from core.services.sport_api_service import SportApiService
from subscriptions.models import Product

logger = logging.getLogger("cron")

allowed_league_ids = [
    39,  # Premier League
    40,  # England Championship
    41,  # England League One
    42,  # England League Two
    45,  # England FA Cup
    78,  # Germany Bundesliga
    79,  # Germany Bundesliga 2
    61,  # France League One
    62,  # France League Two
    66,  # France Coupe de France
    204,  # Turkey Super Lig
    551,  # Turkey 1. Lig
    2,  # World UEFA Champions League
    3,  # World UEFA Europa League
    4,  # World EuroChampionship
    5,  # UEFA Nations League
    848,  # World UEFA Europa Conference League
    135,  # Italy Serie A
    136,  # Italy Serie B
    207,  # Switzerland Super League
    209,  # Switzerland Swiss Cup
    101,  # Japan J-League Cup
    143,  # Spain Copa del Rey
    137,  # Italy Coppa Italia
    88,  # Netherlands Eredivisie
    140,  # Spain La Liga
    141,  # Spain La Liga 2
    94,  # Portugal Primeira Liga
    197,  # Greece Super League
    180,  # Scotland Championship
    179,  # Scotland Premiership
]


class FootballApiService(SportApiService):

    def populate_matches(self, start_date: datetime, end_date: datetime) -> None:
        endpoint = f"{self._get_base_url(SportMatch.SportType.SOCCER)}/fixtures"
        self.fetch_sport_matches(
            start_date,
            end_date,
            endpoint,
            SportMatch.SportType.SOCCER,
            self._process_fixture,
        )

    def fetch_match_prediction(self, external_id: int) -> dict:
        logger.info(f"Fetching predictions for match {external_id}")
        endpoint = f"{self._get_base_url(SportMatch.SportType.SOCCER)}/predictions?fixture={external_id}"
        response = requests.get(
            endpoint, headers=self._get_headers(SportMatch.SportType.SOCCER)
        )

        if response.status_code != 200:
            logger.error(f"Failed to fetch sport matches for url: {endpoint}")
            return {}

        data = response.json()
        data_response = data.get("response")
        if not data_response:
            logger.error(f"No predictions found for match {external_id}")
            return {}

        logger.info(f"Successfully fetched predictions for match {external_id}")
        prediction = data_response[0].get("predictions")
        return prediction

    def fetch_matches_for_league(self):
        return self.populate_matches_for_league(callback=self._process_fixture)

    def _process_fixture(self, item: dict):
        product_obj = Product.objects.get(name=Product.Names.SOCCER)

        fixture = item.get("fixture")
        status = fixture.get("status").get("short")
        league = item.get("league")
        home_team = item.get("teams").get("home")
        away_team = item.get("teams").get("away")
        goals = item.get("goals")

        league_id = league.get("id")

        logger.info(f"Processing fixture with ID: {fixture.get('id')}")

        try:
            league_obj = SportLeague.objects.get(
                external_id=league_id,
                product__name=Product.Names.SOCCER,
            )
        except SportLeague.DoesNotExist:
            logger.error(f"League {league_id} not found")
            return None

        home_team_obj = self._create_or_update_team(
            home_team, league_obj, ApiSportModel.SportType.SOCCER, product_obj
        )
        away_team_obj = self._create_or_update_team(
            away_team, league_obj, ApiSportModel.SportType.SOCCER, product_obj
        )

        home_team_score = goals.get("home")
        away_team_score = goals.get("away")
        if home_team_score is None:
            home_team_score = ""
        if away_team_score is None:
            away_team_score = ""

        kickoff_timestamp = fixture.get("timestamp")

        if not kickoff_timestamp:
            logger.error(f"Match {item.get('id')} has no kickoff timestamp")
            return None

        kickoff_datetime = datetime.fromtimestamp(kickoff_timestamp, tz=timezone.utc)

        match_obj = SportMatch.objects.filter(
            external_id=fixture.get("id"), product=product_obj
        ).first()

        match_status = self._get_status(status)

        if match_obj:
            try:
                match_obj.home_team_score = home_team_score
                match_obj.away_team_score = away_team_score
                match_obj.kickoff_datetime = kickoff_datetime
                match_obj.status = match_status
                match_obj.save()
                logger.info(f"Updated existing match: {match_obj}")
            except Exception as e:
                logger.error(f"Failed to update match: {e}")
                return None
        else:
            try:
                match_obj = SportMatch.objects.create(
                    external_id=fixture.get("id"),
                    league=league_obj,
                    home_team=home_team_obj,
                    away_team=away_team_obj,
                    home_team_score=home_team_score,
                    away_team_score=away_team_score,
                    kickoff_datetime=kickoff_datetime,
                    product=product_obj,
                    type=SportMatch.SportType.SOCCER,
                    status=match_status,
                )
                logger.info(f"Successfully created {match_obj}")
            except Exception as e:
                logger.error(f"Failed to create match: {e}")
                return None

        if (
            match_obj.kickoff_datetime > django_timezone.now()
            and not match_obj.metadata
        ):
            match_obj.metadata = self.fetch_match_prediction(match_obj.external_id)
            match_obj.save()

        return match_obj

    def _get_status(self, status: str) -> SportMatch.Status:
        if status in ["TBD", "NS", "SUSP", "PST", "ABD"]:
            return SportMatch.Status.SCHEDULED
        elif status in ["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"]:
            return SportMatch.Status.IN_PROGRESS
        else:
            return SportMatch.Status.FINISHED
