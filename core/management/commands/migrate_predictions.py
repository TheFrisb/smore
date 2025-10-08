import json
import logging
import os
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand

from core.models import Prediction, SportLeague, SportMatch, SportTeam
from subscriptions.models import Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        json_path = self.get_json_path("data.json")
        self.stdout.write(f"Reading data from {json_path}")

        soccer = Product.objects.get(name=Product.Names.SOCCER)
        # Read data from JSON file
        with open(json_path, "r") as file:
            data = json.load(file)
            leagues = {}

            for item in data:
                # put all leagues in a dictionary to see which is unique
                fields = item.get("fields")
                league_id = fields.get("league")

                # if league id is not a digit, skip
                if not league_id.isdigit():
                    continue

                home_team_name = fields.get("home_team")
                away_team_name = fields.get("away_team")
                prediction = fields.get("prediction")
                odds = fields.get("odds")
                status = fields.get("status")
                visibility = fields.get("visibility")

                # parse YYYY-MM-DD into a datetime object
                kickoff_date = fields.get("kickoff_date")

                formatted_date = datetime.strptime(kickoff_date, "%Y-%m-%d")

                league = SportLeague.objects.filter(external_id=league_id).first()
                if league is None:
                    logger.info(f"League {league_id} not found")
                    logger.info(item)
                    continue

                home_team = SportTeam.objects.filter(name=home_team_name).first()
                if home_team is None:
                    logger.info(f"Home team {home_team_name} not found")
                    continue

                away_team = SportTeam.objects.filter(name=away_team_name).first()
                if away_team is None:
                    logger.info(f"Away team {away_team_name} not found")
                    continue

                match = SportMatch.objects.filter(
                    league=league,
                    home_team=home_team,
                    away_team=away_team,
                    kickoff_datetime__date=formatted_date,
                ).first()

                if match is None:
                    logger.info(
                        f"Match not found for: {league} {home_team} vs {away_team} on {formatted_date}"
                    )
                    logger.info(item)
                    continue

                try:
                    obj = Prediction.objects.create(
                        product=soccer,
                        match=match,
                        prediction=prediction,
                        odds=odds,
                        status=status,
                        visibility=visibility,
                    )

                except Exception as e:
                    # if not duplicate key error, log the error
                    if "duplicate key" not in str(e):
                        logger.error(f"Failed to create prediction: {e}")
                        logger.error(item)

            self.stdout.write(f"Found {len(leagues)} unique leagues")

            # print all unique leagues
            for league in leagues:
                self.stdout.write(f"League: {league}")

    def get_json_path(self, filename):
        return os.path.join(settings.BASE_DIR, filename)
