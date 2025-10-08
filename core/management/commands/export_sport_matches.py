import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from core.models import (  # Replace 'your_app' with your app name
    ApiSportModel,
    SportMatch,
)

BATCH_SIZE = 5000  # Adjust based on your memory constraints


class Command(BaseCommand):
    help = "Export sport matches to JSON file in batches"

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str, help="Output JSON file path")

    def handle(self, *args, **kwargs):
        output_file = kwargs["output_file"]
        total_matches = SportMatch.objects.filter(
            type=ApiSportModel.SportType.SOCCER
        ).count()
        processed = 0

        with open(output_file, "w") as f:
            f.write("[")  # Start of JSON array

            first = True
            while processed < total_matches:
                matches = (
                    SportMatch.objects.filter(type=ApiSportModel.SportType.SOCCER)
                    .select_related("league", "home_team", "away_team")
                    .only(
                        "external_id",
                        "league__external_id",
                        "home_team__external_id",
                        "home_team_score",
                        "away_team_score",
                        "away_team__external_id",
                        "kickoff_datetime",
                        "metadata",
                    )
                    .order_by("id")[processed : processed + BATCH_SIZE]
                )

                batch_data = []
                for match in matches:
                    batch_data.append(
                        {
                            "external_id": match.external_id,
                            "league_external_id": match.league.external_id,
                            "home_team_external_id": match.home_team.external_id,
                            "home_team_score": match.home_team_score,
                            "away_team_score": match.away_team_score,
                            "away_team_external_id": match.away_team.external_id,
                            "kickoff_datetime": match.kickoff_datetime.isoformat(),
                            "metadata": match.metadata,
                        }
                    )

                json_batch = json.dumps(batch_data, cls=DjangoJSONEncoder)[1:-1]
                if not first:
                    f.write(",")
                f.write(json_batch)

                processed += len(matches)
                self.stdout.write(f"Processed {processed}/{total_matches} matches...")
                first = False

            f.write("]")  # End of JSON array

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully exported {total_matches} matches to {output_file}"
            )
        )
