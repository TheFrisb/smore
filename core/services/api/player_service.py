import json
from datetime import datetime

from core.models import Player, Product, ApiSportModel
from core.services.api.in_progress.BaseApiFootballService import BaseApiFootballService


class PlayerService(BaseApiFootballService):

    def fetch_player_profiles(self):
        """
        Fetches player profiles from the API.
        """
        endpoint = "players/profiles"
        current_page = 1
        max_pages = 2

        product = Product.objects.filter(name=Product.Names.SOCCER).first()

        while current_page <= max_pages:
            response = self.get_endpoint(endpoint=endpoint, query_params={"page": current_page})
            paging = response.get("paging", {})
            body = response.get("response", [])

            if not body:
                self.log.info("No more player profiles found.")
                break

            max_pages = paging.get("total")
            current_page += 1
            print("Current page:", current_page)

            for item in body:
                data = item.get("player", {})
                if not data:
                    self.log.warning(f"No player data found for item: {item}")
                    continue

                birth_date_string = None
                birth_place = None
                birth_country = None
                print(json.dumps(data, indent=2))

                if data["birth"]:
                    birth_date_string = data["birth"].get("date")
                    birth_place = data["birth"].get("place")
                    birth_country = data["birth"].get("country")

                Player.objects.create(
                    product=product,
                    type=ApiSportModel.SportType.TEMP_FIX,
                    external_id=data["id"],
                    name=data["name"],
                    first_name=data["firstname"],
                    last_name=data["lastname"],
                    age=data["age"],
                    birth_date=datetime.strptime(birth_date_string, "%Y-%m-%d") if birth_date_string else None,
                    birth_place=birth_place,
                    birth_country=birth_country,
                    nationality=data["nationality"],
                    height=data["height"],
                    weight=data["weight"],
                    number=data["number"],
                    position=data["position"],
                    photo=None
                )
