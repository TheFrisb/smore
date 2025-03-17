import logging
import os
from datetime import datetime, timedelta, timezone

import requests

from backend import settings
from core.models import SportCountry, Product, SportLeague, SportTeam, SportMatch

logger = logging.getLogger(__name__)


class BasketballApiService:
    def __init__(self):
        self.base_url = "https://api-basketball.p.rapidapi.com"
        self.rapidapi_host = "api-basketball.p.rapidapi.com"
        self.rapidapi_key = settings.RAPIDAPI_BASKETBALL_KEY

    def _get_headers(self):
        return {
            "x-rapidapi-host": self.rapidapi_host,
            "x-rapidapi-key": self.rapidapi_key,
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

        print(endpoint)
        print(data)

        for item in data.get("response"):
            country = item.get("country")

            league_name = item.get("name")
            league_id = item.get("id")

            league_type = item.get("type")
            league_logo_url = item.get("logo")

            country_name = country.get("name")
            print(country_name)
            country_obj = SportCountry.objects.get(name=country_name)

            league_logo_path = self._download_asset(
                league_logo_url,
                f"assets/leagues/logos/",
                f"{league_id}-{Product.Names.BASKETBALL}.png",
            )

            try:
                SportLeague.objects.create(
                    external_id=league_id,
                    name=league_name,
                    country=country_obj,
                    league_type=league_type,
                    logo=league_logo_path,
                    product=Product.objects.get(name=Product.Names.BASKETBALL),
                )
                logger.info(f"Created league: {league_name}")
            except Exception as e:
                logger.error(f"Failed to create league: {league_name} - {e}")

    def populate_upcoming_matches(self):
        start_date = datetime.now()
        logger.info(f"Fetching sport matches from start_date: {start_date}")

        for i in range(10):
            date = start_date + timedelta(days=i)
            formatted_date = date.strftime("%Y-%m-%d")
            endpoint = f"{self.base_url}/games?date={formatted_date}"
            logger.info(f"Fetching basketball sport matches from endpoint: {endpoint}")
            response = requests.get(endpoint, headers=self._get_headers())

            if response.status_code != 200:
                logger.error(f"Failed to fetch sport matches for url: {endpoint}")
                continue

            data = response.json()
            for item in data.get("response"):
                self._process_fixture(item)

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

        league_obj = SportLeague.objects.get(
            external_id=league_id, product__name=Product.Names.BASKETBALL
        )
        home_team_obj = self._create_or_update_team(
            item.get("teams").get("home"), league_obj
        )
        away_team_obj = self._create_or_update_team(
            item.get("teams").get("away"), league_obj
        )

        try:
            match_obj = SportMatch.objects.create(
                external_id=external_id,
                league=league_obj,
                home_team=home_team_obj,
                away_team=away_team_obj,
                home_team_score=home_team_score,
                away_team_score=away_team_score,
                kickoff_datetime=kickoff_datetime,
                product=Product.objects.get(name=Product.Names.BASKETBALL),
            )
            logger.info(f"Successfully created {match_obj}")
        except Exception as e:
            logger.error(f"Failed to create match: {e}")
            return None

        return match_obj

    def _create_or_update_team(self, team_data, league_obj):
        team_id = team_data.get("id")
        team_name = team_data.get("name")
        team_logo_url = team_data.get("logo")

        team_logo_path = self._download_asset(
            team_logo_url,
            f"assets/teams/logos/",
            f"{team_id}-{Product.Names.BASKETBALL}.png",
        )

        try:
            team_obj, created = SportTeam.objects.get_or_create(
                external_id=team_id,
                product=Product.objects.get(name=Product.Names.BASKETBALL),
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
