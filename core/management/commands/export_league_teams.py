import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from core.models import SportLeagueTeam  # Replace 'your_app' with your app name

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Export SportLeagueTeam relationships to JSON file"

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str, help="Output JSON file path")

    def handle(self, *args, **kwargs):
        output_file = kwargs["output_file"]
        total = SportLeagueTeam.objects.count()
        processed = 0

        with open(output_file, "w") as f:
            f.write("[")  # Start of JSON array
            first = True

            while processed < total:
                # Optimized query with prefetching
                league_teams = (
                    SportLeagueTeam.objects.select_related("league", "team")
                    .only(
                        "season",
                        "league__external_id",
                        "league__type",
                        "team__external_id",
                        "team__type",
                    )
                    .order_by("id")[processed : processed + BATCH_SIZE]
                )

                batch_data = []
                for lt in league_teams:
                    batch_data.append(
                        {
                            "league_external_id": lt.league.external_id,
                            "league_type": lt.league.type,
                            "team_external_id": lt.team.external_id,
                            "team_type": lt.team.type,
                            "season": lt.season,
                        }
                    )

                json_batch = json.dumps(batch_data, cls=DjangoJSONEncoder)[1:-1]
                if not first:
                    f.write(",")
                f.write(json_batch)

                processed += len(league_teams)
                self.stdout.write(
                    f"Processed {processed}/{total} league-team relationships..."
                )
                first = False

            f.write("]")  # End of JSON array

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {total} league-team relationships to {output_file}"
            )
        )
