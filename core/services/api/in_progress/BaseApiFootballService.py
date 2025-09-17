import logging
import os
from abc import ABC
from typing import Optional
from urllib.parse import urlencode

import requests

from backend import settings


class BaseApiFootballService(ABC):
    def __init__(self):
        self.log = logging.getLogger("cron")

    def _get_headers(self):
        return {
            "x-rapidapi-host": settings.RAPIDAPI_SOCCER_HOST,
            "x-rapidapi-key": settings.RAPIDAPI_SOCCER_KEY,
        }

    def _get_base_url(self):
        return f"https://{settings.RAPIDAPI_SOCCER_HOST}/v3"

    def get_endpoint(self, endpoint: str, query_params: dict = None) -> dict:
        query = urlencode(query_params, doseq=True) if query_params else ""
        url = (
            f"{self._get_base_url()}/{endpoint}?{query}"
            if query
            else f"{self._get_base_url()}/{endpoint}"
        )
        response = requests.get(url=url, headers=self._get_headers())

        if response.status_code != 200:
            self.log.error(
                f"Error fetching data from {url}: {response.status_code} - {response.text}"
            )
            response.raise_for_status()

        return response.json()

    def _download_asset(
        self, asset_url: str, upload_dir: str, filename: str
    ) -> Optional[str]:
        if not asset_url:
            self.log.error("Asset URL is empty.")
            return None

        try:
            self.log.info(f"Downloading asset: {asset_url}")
            flag_response = requests.get(asset_url, stream=True, timeout=10)
            flag_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log.error(f"Failed to download asset: {asset_url}. Error: {e}")
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

        self.log.error(f"Failed to download asset: {asset_url}")

        return None
