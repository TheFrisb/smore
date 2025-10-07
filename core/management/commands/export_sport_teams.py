import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from core.models import ApiSportModel, SportTeam

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Export sport teams with league relationships and standings to JSON"

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str, help="Output JSON file path")

    def handle(self, *args, **kwargs):
        output_file = kwargs["output_file"]
        total_teams = SportTeam.objects.filter(
            type=ApiSportModel.SportType.SOCCER
        ).count()
        processed = 0

        with open(output_file, "w") as f:
            f.write("[")
            first = True

            while processed < total_teams:
                teams = (
                    SportTeam.objects.filter(type=ApiSportModel.SportType.SOCCER)
                    .prefetch_related("team_leagues__league", "team_leagues__standings")
                    .order_by("id")[processed : processed + BATCH_SIZE]
                )

                batch_data = []
                for team in teams:
                    leagues_data = []
                    for lt in team.team_leagues.all():
                        leagues_data.append(
                            {
                                "league_external_id": lt.league.external_id,
                                "season": lt.season,
                                "standings_data": (
                                    lt.standings.data
                                    if hasattr(lt, "standings") and lt.standings
                                    else None
                                ),
                            }
                        )

                    batch_data.append(
                        {
                            "external_id": team.external_id,
                            "name": team.name,
                            "logo": team.logo.name if team.logo else None,
                            "product_id": team.product_id,
                            "type": team.type,
                            "leagues": leagues_data,
                        }
                    )

                json_batch = json.dumps(batch_data, cls=DjangoJSONEncoder)[1:-1]
                if not first:
                    f.write(",")
                f.write(json_batch)

                processed += len(teams)
                self.stdout.write(f"Processed {processed}/{total_teams} teams...")
                first = False

            f.write("]")

        self.stdout.write(
            self.style.SUCCESS(f"Exported {total_teams} teams to {output_file}")
        )
