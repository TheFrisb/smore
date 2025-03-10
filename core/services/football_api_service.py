import logging
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from django.utils import timezone as django_timezone

from core.models import SportCountry, SportLeague, SportTeam, SportMatch, Prediction

logger = logging.getLogger(__name__)

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


class FootballApiService:
    def __init__(self):
        self.base_url = settings.RAPIDAPI_HOST
        self.rapidapi_host = settings.RAPIDAPI_HOST
        self.rapidapi_key = settings.RAPIDAPI_KEY

    def _get_headers(self):
        return {
            # "x-rapidapi-host": settings.RAPIDAPI_HOST,
            # "x-rapidapi-key": settings.RAPIDAPI_KEY,
            "x-apisports-key": settings.RAPIDAPI_KEY,
        }

    def populate_countries(self):
        endpoint = f"{self.base_url}/countries"
        response = requests.get(endpoint, headers=self._get_headers())
        data = response.json()

        for country in data.get("response", []):
            name = country.get("name")
            code = country.get("code")
            flag_url = country.get("flag")

            if code is None:
                code = ""

            flag_path = self._download_asset(flag_url, "assets/flags", f"{code}.svg")
            try:
                SportCountry.objects.create(name=name, code=code, logo=flag_path)
                logger.info(f"Created country: {name}")
            except Exception as e:
                logger.error(f"Failed to create country: {name} - {e}")

    def populate_leagues(self):
        endpoint = f"{self.base_url}/leagues"
        response = requests.get(endpoint, headers=self._get_headers())
        data = response.json()

        for item in data.get("response"):
            league = item.get("league")
            country = item.get("country")

            league_name = league.get("name")
            league_id = league.get("id")

            league_type = league.get("type")
            league_logo_url = league.get("logo")

            country_name = country.get("name")
            country_obj = SportCountry.objects.get(name=country_name)

            league_logo_path = self._download_asset(
                league_logo_url, f"assets/leagues/logos/", f"{league_id}.png"
            )

            try:
                SportLeague.objects.create(
                    external_id=league_id,
                    name=league_name,
                    country=country_obj,
                    league_type=league_type,
                    logo=league_logo_path,
                )
                logger.info(f"Created league: {league_name}")
            except Exception as e:
                logger.error(f"Failed to create league: {league_name} - {e}")

    def populate_matches_per_league_id(self, league_id: int):
        start_season = 2022
        end_season = 2026

        for season in range(start_season, end_season):
            if season == 2025:
                logger.info(f"Marking league ID: {league_id} as processed")
                league_obj = SportLeague.objects.get(external_id=league_id)
                league_obj.is_processed = True
                league_obj.save()
                break
            endpoint = f"{self.base_url}/fixtures?league={league_id}&season={season}"
            logger.info(f"Fetching sport matches from endpoint: {endpoint}")
            response = requests.get(endpoint, headers=self._get_headers())

            if response.status_code != 200:
                logger.error(f"Failed to fetch sport matches for url: {endpoint}")
                continue

            data = response.json()
            for item in data.get("response"):
                match_obj = self._process_fixture(item)

                if match_obj is None:
                    if season < 2024:
                        match_obj = SportMatch.objects.filter(
                            external_id=item.get("fixture").get("id")
                        ).first()
                        if match_obj:
                            logger.info(
                                f"Marking league ID: {league_id} as processed because match {match_obj.external_id} [{match_obj.kickoff_datetime}] already exists"
                            )
                            league_obj = SportLeague.objects.get(external_id=league_id)
                            league_obj.is_processed = True
                            league_obj.save()
                            logger.info(f"Marked league ID: {league_id} as processed")
                            break

                    logger.error(
                        f"Failed to process fixture {item.get('fixture').get('id')}"
                    )
                    continue

                if match_obj.kickoff_datetime > django_timezone.now():
                    match_obj.metadata = self.fetch_match_prediction(
                        match_obj.external_id
                    )
                    match_obj.save()

    def populate_upcoming_matches(self):
        start_date = datetime.now()
        logger.info(f"Fetching sport matches from start_date: {start_date}")

        for i in range(2):
            date = start_date + timedelta(days=i)
            formatted_date = date.strftime("%Y-%m-%d")
            endpoint = f"{self.base_url}/fixtures?date={formatted_date}"
            logger.info(f"Fetching sport matches from endpoint: {endpoint}")
            response = requests.get(endpoint, headers=self._get_headers())

            if response.status_code != 200:
                logger.error(f"Failed to fetch sport matches for url: {endpoint}")
                continue

            data = response.json()
            for item in data.get("response"):
                match_obj = self._process_fixture(item)

                if match_obj is None:
                    continue

                if match_obj.kickoff_datetime > django_timezone.now():
                    match_obj.metadata = self.fetch_match_prediction(
                        match_obj.external_id
                    )
                    match_obj.save()

    def fetch_match_prediction(self, external_id: int) -> dict:
        logger.info(f"Fetching predictions for match {external_id}")
        endpoint = f"{self.base_url}/predictions?fixture={external_id}"
        response = requests.get(endpoint, headers=self._get_headers())

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

    def _process_fixture(self, item: dict):
        fixture = item.get("fixture")
        league = item.get("league")
        home_team = item.get("teams").get("home")
        away_team = item.get("teams").get("away")
        goals = item.get("goals")

        league_id = league.get("id")

        logger.info(f"Processing fixture with ID: {fixture.get('id')}")

        try:
            league_obj = SportLeague.objects.get(external_id=league_id)
        except SportLeague.DoesNotExist:
            logger.error(f"League {league_id} not found")
            return None

        home_team_obj = self._create_or_update_team(home_team, league_obj)
        away_team_obj = self._create_or_update_team(away_team, league_obj)

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

        try:
            match_obj = SportMatch.objects.create(
                external_id=fixture.get("id"),
                league=league_obj,
                home_team=home_team_obj,
                away_team=away_team_obj,
                home_team_score=home_team_score,
                away_team_score=away_team_score,
                kickoff_datetime=kickoff_datetime,
            )
            logger.info(f"Successfully created {match_obj}")
        except Exception as e:
            logger.error(f"Failed to create match: {e}")
            return None

        return match_obj

    def update_prediction_scores(self):
        predictions = Prediction.objects.filter(match__home_team_score="").order_by(
            "-match__kickoff_datetime"
        )
        logger.info(f"Found {predictions.count()} predictions without scores")

        for prediction in predictions:
            time.sleep(5)
            sport_match = prediction.match
            sport_match_external_id = sport_match.external_id

            endpoint = f"{self.base_url}/fixtures?id={sport_match_external_id}"
            response = requests.get(endpoint, headers=self.get_headers())

            if response.status_code != 200:
                logger.error(f"Failed to fetch sport matches for url: {endpoint}")
                continue

            data = response.json()
            score = data.get("response")[0].get("score").get("fulltime")
            home_team_score = score.get("home")
            away_team_score = score.get("away")

            if home_team_score is None or away_team_score is None:
                logger.info(
                    f"Skipping match {sport_match_external_id}, as it has no score"
                )
                continue

            sport_match.home_team_score = home_team_score
            sport_match.away_team_score = away_team_score

            sport_match.save()
            logger.info(
                f"Successfully updated match {sport_match_external_id} with score {home_team_score} - {away_team_score}"
            )

    def _create_or_update_team(self, team_data, league_obj):
        team_id = team_data.get("id")
        team_name = team_data.get("name")
        team_logo_url = team_data.get("logo")

        team_logo_path = self._download_asset(
            team_logo_url, f"assets/teams/logos/", f"{team_id}.png"
        )

        try:
            team_obj, created = SportTeam.objects.get_or_create(
                external_id=team_id,
                defaults={
                    "name": team_name,
                    "league": league_obj,
                    "logo": team_logo_path,
                },
            )
            return team_obj
        except Exception as e:
            logger.error(f"Failed to create team {team_name}: {e}")
            return None

    def _download_asset(self, asset_url, upload_dir, filename):
        if not asset_url:
            return None

        flag_response = requests.get(asset_url, stream=True)
        if flag_response.status_code == 200:
            flag_dir = os.path.join(settings.MEDIA_ROOT, upload_dir)
            os.makedirs(flag_dir, exist_ok=True)

            flag_filename = filename
            flag_path = os.path.join(upload_dir, flag_filename)
            full_flag_path = os.path.join(settings.MEDIA_ROOT, flag_path)
            with open(full_flag_path, "wb") as f:
                for chunk in flag_response.iter_content(1024):
                    f.write(chunk)

            return flag_path
