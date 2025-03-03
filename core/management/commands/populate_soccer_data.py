import logging
import os
from datetime import datetime, timezone, timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import SportCountry, SportLeague, SportTeam, SportMatch

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
    94,  # Portugal Primeira Liga
    197,  # Greece Super League
    180,  # Scotland Championship
    179,  # Scotland Premiership
]


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        self.populate_teams()

    def populate_countries(self):
        endpoint = "https://api-football-v1.p.rapidapi.com/v3/countries"
        response = requests.get(endpoint, headers=self.get_headers())
        data = response.json()

        for country in data.get("response", []):
            name = country.get("name")
            code = country.get("code")
            flag_url = country.get("flag")

            if code is None:
                code = ""

            flag_path = self.download_asset(flag_url, "assets/flags", f"{code}.svg")
            obj = SportCountry.objects.create(name=name, code=code, logo=flag_path)
            self.stdout.write(f"Successfully created {obj}")

    def populate_leagues(self):
        endpoint = "https://api-football-v1.p.rapidapi.com/v3/leagues"
        response = requests.get(endpoint, headers=self.get_headers())
        data = response.json()

        for item in data.get("response"):
            league = item.get("league")
            country = item.get("country")

            league_name = league.get("name")
            league_id = league.get("id")

            if league_id not in allowed_league_ids:
                logger.info(
                    f"Skipping league {league_id}, as it is not in the allowed list"
                )
                continue

            league_type = league.get("type")
            league_logo_url = league.get("logo")

            country_name = country.get("name")
            country_obj = SportCountry.objects.get(name=country_name)

            league_logo_path = self.download_asset(
                league_logo_url, f"assets/leagues/logos/", f"{league_id}.png"
            )

            obj = SportLeague.objects.create(
                external_id=league_id,
                name=league_name,
                country=country_obj,
                league_type=league_type,
                logo=league_logo_path,
            )
            self.stdout.write(f"Successfully created {obj}")

    def populate_teams(self):
        # make start date 9 january
        start_date = datetime(2025, 1, 9)

        # loop over next 5 days
        for i in range(60):
            date = start_date + timedelta(days=i)
            formatted_date = date.strftime("%Y-%m-%d")
            endpoint = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={formatted_date}"
            logger.info(f"Fetching sport matches from endpoint: {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers())

            if response.status_code != 200:
                logger.error(f"Failed to fetch sport matches for url: {endpoint}")
                continue

            data = response.json()

            for item in data.get("response"):
                fixture = item.get("fixture")
                league = item.get("league")
                home_team = item.get("teams").get("home")
                away_team = item.get("teams").get("away")

                league_id = league.get("id")

                if league_id not in allowed_league_ids:
                    logger.info(
                        f"Skipping league {league_id}, as it is not in the allowed list"
                    )
                    continue
                logger.info(f"Processing fixture {fixture.get('id')}")

                league_obj = SportLeague.objects.get(external_id=league_id)

                home_team_obj = self.create_or_update_team(home_team, league_obj)
                away_team_obj = self.create_or_update_team(away_team, league_obj)

                kickoff_timestamp = fixture.get("timestamp")

                kickoff_datetime = datetime.fromtimestamp(
                    kickoff_timestamp, tz=timezone.utc
                )

                match_obj = SportMatch.objects.create(
                    external_id=fixture.get("id"),
                    league=league_obj,
                    home_team=home_team_obj,
                    away_team=away_team_obj,
                    kickoff_datetime=kickoff_datetime,
                )

                self.stdout.write(f"Successfully created {match_obj}")

    def create_or_update_team(self, team_data, league_obj):
        team_id = team_data.get("id")
        team_name = team_data.get("name")
        team_logo_url = team_data.get("logo")

        team_logo_path = self.download_asset(
            team_logo_url, f"assets/teams/logos/", f"{team_id}.png"
        )

        # team_obj, created = SportTeam.objects.get_or_create(
        #     external_id=team_id,
        #     name=team_name,
        #     league=league_obj,
        #     defaults={"logo": team_logo_path},
        # )

        team_obj = SportTeam.objects.filter(external_id=team_id).first()
        if not team_obj:
            team_obj = SportTeam.objects.create(
                external_id=team_id,
                name=team_name,
                league=league_obj,
                logo=team_logo_path,
            )

        self.stdout.write(f"Successfully created {team_obj}")
        return team_obj

    def download_asset(self, asset_url, upload_dir, filename):
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

    def get_headers(self):
        return {
            "x-rapidapi-host": settings.RAPIDAPI_HOST,
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
        }
