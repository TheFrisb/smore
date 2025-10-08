import json
import os

from django.core.files import File
from django.core.management.base import BaseCommand

from backend import settings
from core.models import (
    ApiSportModel,
    SportLeague,
    SportLeagueTeam,
    SportTeam,
    TeamStanding,
)
from subscriptions.models import Product

BATCH_SIZE = 2000


class Command(BaseCommand):
    help = "Import sport teams with league relationships and standings from JSON"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=str, help="Input JSON file path")

    def handle(self, *args, **kwargs):
        input_file = kwargs["input_file"]
        media_root = settings.MEDIA_ROOT

        leagues = SportLeague.objects.values("id", "external_id")
        league_map = {l["external_id"]: l["id"] for l in leagues}

        with open(input_file, "r") as f:
            teams_data = json.load(f)

        product_id = Product.objects.get(name=Product.Names.SOCCER).id
        total = len(teams_data)
        self.stdout.write(f"Importing {total} teams...")

        teams_to_create = []
        league_links = []
        standings_to_create = []

        for i, team_data in enumerate(teams_data, 1):
            team_obj = SportTeam(
                external_id=team_data["external_id"],
                name=team_data["name"],
                product_id=product_id,
                type=ApiSportModel.SportType.SOCCER,
            )

            # Handle logo
            if team_data["logo"]:
                logo_path = os.path.join(media_root, team_data["logo"])
                if os.path.exists(logo_path):
                    with open(logo_path, "rb") as logo_file:
                        team_obj.logo.save(
                            os.path.basename(team_data["logo"]),
                            File(logo_file),
                            save=False,
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Team {team_data['name']}: Logo file {logo_path} not found"
                        )
                    )

            teams_to_create.append(team_obj)

            # Batch commit
            if i % BATCH_SIZE == 0 or i == total:
                SportTeam.objects.bulk_create(teams_to_create, batch_size=BATCH_SIZE)

                created_teams = SportTeam.objects.filter(
                    external_id__in=[t.external_id for t in teams_to_create]
                )
                created_map = {t.external_id: t.id for t in created_teams}

                # Create leagues & standings
                for t_data in teams_to_create:
                    for l_data in next(
                        td
                        for td in teams_data
                        if td["external_id"] == t_data.external_id
                    )["leagues"]:
                        league_id = league_map.get(l_data["league_external_id"])
                        if league_id:
                            slt = SportLeagueTeam(
                                league_id=league_id,
                                team_id=created_map[t_data.external_id],
                                season=l_data["season"],
                            )
                            league_links.append(slt)

                            if l_data.get("standings_data"):
                                standings_to_create.append(
                                    TeamStanding(
                                        league_team=slt, data=l_data["standings_data"]
                                    )
                                )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"League {l_data['league_external_id']} not found for team {t_data.name}"
                                )
                            )

                SportLeagueTeam.objects.bulk_create(league_links, batch_size=BATCH_SIZE)
                TeamStanding.objects.bulk_create(
                    standings_to_create, batch_size=BATCH_SIZE
                )

                self.stdout.write(f"Imported {i}/{total} teams...")

                teams_to_create = []
                league_links = []
                standings_to_create = []

        self.stdout.write(self.style.SUCCESS(f"Finished importing {total} teams"))
