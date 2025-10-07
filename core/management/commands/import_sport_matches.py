import json

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from core.models import ApiSportModel, SportLeague, SportMatch, SportTeam
from subscriptions.models import Product

BATCH_SIZE = 2000


class Command(BaseCommand):
    help = "Import sport matches from JSON file"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=str, help="Input JSON file path")

    def handle(self, *args, **kwargs):
        input_file = kwargs["input_file"]

        # Preload lookup mappings
        leagues = SportLeague.objects.values("id", "external_id")
        teams = SportTeam.objects.values("id", "external_id")

        league_map = {l["external_id"]: l["id"] for l in leagues}
        team_map = {t["external_id"]: t["id"] for t in teams}

        with open(input_file, "r") as f:
            matches_data = json.load(f)

        total = len(matches_data)
        self.stdout.write(f"Importing {total} matches...")
        product = Product.objects.get(name=Product.Names.SOCCER)

        matches_to_create = []
        for i, match in enumerate(matches_data, 1):
            try:
                matches_to_create.append(
                    SportMatch(
                        product=product,
                        type=ApiSportModel.SportType.SOCCER,
                        external_id=match["external_id"],
                        league_id=league_map[match["league_external_id"]],
                        home_team_id=team_map[match["home_team_external_id"]],
                        home_team_score=match["home_team_score"],
                        away_team_score=match["away_team_score"],
                        away_team_id=team_map[match["away_team_external_id"]],
                        kickoff_datetime=parse_datetime(match["kickoff_datetime"]),
                        metadata=match.get("metadata") or {},
                    )
                )
            except KeyError as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Match {match['external_id']}: Missing reference ({e})"
                    )
                )

            # Batch commit
            if i % BATCH_SIZE == 0 or i == total:
                SportMatch.objects.bulk_create(
                    matches_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True
                )
                self.stdout.write(f"Imported {i}/{total} matches...")
                matches_to_create = []

        self.stdout.write(self.style.SUCCESS(f"Finished importing {total} matches"))
