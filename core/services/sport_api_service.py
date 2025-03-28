import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from django.conf import settings

from core.models import ApiSportModel, SportLeague, SportCountry, Product, SportTeam

logger = logging.getLogger(__name__)


class SportApiService:
    def _get_headers(self, sport_type: ApiSportModel.SportType) -> dict:
        if sport_type == ApiSportModel.SportType.BASKETBALL:
            return {
                "x-rapidapi-host": settings.RAPIDAPI_BASKETBALL_HOST,
                "x-rapidapi-key": settings.RAPIDAPI_BASKETBALL_KEY,
            }
        elif sport_type == ApiSportModel.SportType.SOCCER:
            return {
                "x-rapidapi-host": settings.RAPIDAPI_SOCCER_HOST,
                "x-rapidapi-key": settings.RAPIDAPI_SOCCER_KEY,
            }

        elif sport_type == ApiSportModel.SportType.NHL:
            return {
                "x-rapidapi-host": settings.RAPIDAPI_NHL_HOST,
                "x-rapidapi-key": settings.RAPIDAPI_NHL_KEY,
            }

        raise ValueError(
            f"Unsupported sport type: {sport_type}. Supported types are: {list(ApiSportModel.SportType)}"
        )

    def _get_base_url(self, sport_type: ApiSportModel.SportType) -> str:
        if sport_type == ApiSportModel.SportType.BASKETBALL:
            return f"https://{settings.RAPIDAPI_BASKETBALL_HOST}"

        elif sport_type == ApiSportModel.SportType.SOCCER:
            return f"https://{settings.RAPIDAPI_SOCCER_HOST}"

        elif sport_type == ApiSportModel.SportType.NHL:
            return f"https://{settings.RAPIDAPI_NHL_HOST}"

        raise ValueError(
            f"Unsupported sport type: {sport_type}. Supported types are: {list(ApiSportModel.SportType)}"
        )

    def populate_countries(self, sport_type: ApiSportModel.SportType) -> None:
        endpoint = f"{self._get_base_url(sport_type)}/countries"
        headers = self._get_headers(sport_type)
        response = requests.get(endpoint, headers=headers)
        data = response.json()

        for country in data.get("response", []):
            country_name = country.get("name")
            country_code = country.get("code")
            country_flag_url = country.get("flag")

            if country_code is None:
                logger.error("Country code is missing for country: %s", country_name)
                country_code = ""

            flag_path = self._download_asset(
                country_flag_url,
                upload_dir=f"countries/{sport_type.value}/",
                filename=f"{country_code}.png",
            )

            if flag_path is None:
                logger.error(
                    "Failed to download flag for country: %s with code: %s",
                    country_name,
                    country_code,
                )

            try:
                SportCountry.objects.create(
                    name=country_name, code=country_code, logo=flag_path
                )
                logger.info(f"Created country: {country_name}")
            except Exception as e:
                logger.error(
                    f"Failed to create country: {country_name} with code: {country_code}. Error: {e}"
                )

    def populate_leagues(
            self, sport_type: ApiSportModel.SportType, product: Product
    ) -> None:
        endpoint = f"{self._get_base_url(sport_type)}/leagues"
        print(f"Endpoint: {endpoint}")
        headers = self._get_headers(sport_type)
        response = requests.get(endpoint, headers=headers)
        data = response.json()

        for item in data.get("response"):
            country = item.get("country")
            country_name = country.get("name")
            country_obj = SportCountry.objects.get(name=country_name)

            if sport_type is not ApiSportModel.SportType.SOCCER:
                league_id = item.get("id")
                league_name = item.get("name")
                league_type = item.get("type")
                league_logo_url = item.get("logo")
            else:
                league = item.get("league")
                league_id = league.get("id")
                league_name = league.get("name")
                league_type = league.get("type")
                league_logo_url = league.get("logo")

            league_logo_path = self._download_asset(
                league_logo_url,
                f"assets/leagues/logos/",
                f"{league_id}-{sport_type}.png",
            )

            try:
                SportLeague.objects.create(
                    external_id=league_id,
                    type=sport_type,
                    name=league_name,
                    country=country_obj,
                    league_type=league_type,
                    logo=league_logo_path,
                    product=product,
                )
                logger.info(f"Created league: {league_name}")
            except Exception as e:
                logger.error(f"Failed to create league: {league_name} - {e}")

    def _get_league_obj(
            self, external_id: int, sport_type: ApiSportModel.SportType
    ) -> Optional[SportLeague]:
        """
        Get the league object based on sport type and external ID.
        """
        try:
            league = SportLeague.objects.get(type=sport_type, external_id=external_id)
            return league
        except SportLeague.DoesNotExist:
            logger.error(
                f"League with external ID: {external_id} for sport: {sport_type} not found."
            )
            return None

    def fetch_sport_matches(
            self,
            start_date: Optional[datetime],
            end_date: Optional[datetime],
            endpoint: str,
            sport_type: ApiSportModel.SportType,
            process_match: callable,
    ) -> None:
        if start_date is None:
            start_date = datetime.today() - timedelta(days=1)
        if end_date is None:
            end_date = start_date + timedelta(days=9)

        logger.info(f"Fetching {sport_type} matches from {start_date} to {end_date}")

        current_date = start_date
        while current_date <= end_date:
            logger.info(f"Fetching {sport_type} matches for date: {current_date}")
            formatted_date = current_date.strftime("%Y-%m-%d")
            query_endpoint = f"{endpoint}?date={formatted_date}"
            logger.info(
                f"Fetching {sport_type} matches from endpoint: {query_endpoint}"
            )
            headers = self._get_headers(sport_type)
            response = requests.get(query_endpoint, headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch {sport_type} matches from endpoint: {query_endpoint}. Status code: {response.status_code}"
                )
                current_date += timedelta(days=1)
                continue

            data = response.json()
            for item in data.get("response"):
                process_match(item)

            current_date += timedelta(days=1)

    def _create_or_update_team(
            self,
            team_data: dict,
            league_obj: SportLeague,
            sport_type: ApiSportModel.SportType,
            product: Product,
    ) -> Optional[SportTeam]:
        team_id = team_data.get("id")
        team_name = team_data.get("name")
        team_logo_url = team_data.get("logo")

        team_logo_path = self._download_asset(
            team_logo_url,
            f"assets/teams/logos/",
            f"{team_id}-{league_obj.type}.png",
        )

        try:
            team_obj, created = SportTeam.objects.get_or_create(
                external_id=team_id,
                type=sport_type,
                defaults={
                    "name": team_name,
                    "league": league_obj,
                    "logo": team_logo_path,
                    "product": product,
                },
            )
            return team_obj
        except Exception as e:
            logger.error(f"Failed to create team {team_name}: {e}")
            return None

    def _download_asset(
            self, asset_url: str, upload_dir: str, filename: str
    ) -> Optional[str]:
        if not asset_url:
            logger.error("Asset URL is empty.")
            return None

        try:
            logger.info(f"Downloading asset: {asset_url}")
            flag_response = requests.get(asset_url, stream=True, timeout=10)
            flag_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download asset: {asset_url}. Error: {e}")
            return None

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

        logger.error(f"Failed to download asset: {asset_url}")

        return None
