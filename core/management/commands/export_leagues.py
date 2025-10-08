import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from core.models import ApiSportModel, SportLeague

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Export sport leagues to JSON file"

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str, help="Output JSON file path")

    def handle(self, *args, **kwargs):
        output_file = kwargs["output_file"]
        total_leagues = SportLeague.objects.filter(
            type=ApiSportModel.SportType.SOCCER
        ).count()
        processed = 0

        with open(output_file, "w") as f:
            f.write("[")
            first = True

            while processed < total_leagues:
                leagues = (
                    SportLeague.objects.filter(type=ApiSportModel.SportType.SOCCER)
                    .select_related("product", "country")
                    .only(
                        "external_id",
                        "name",
                        "logo",
                        "product__id",
                        "country__name",
                        "league_type",
                        "current_season_id",
                        "is_processed",
                        "type",
                    )
                    .order_by("id")[processed : processed + BATCH_SIZE]
                )

                batch_data = []
                for league in leagues:
                    batch_data.append(
                        {
                            "external_id": league.external_id,
                            "name": league.name,
                            "logo": league.logo.name if league.logo else None,
                            "product_id": league.product_id,
                            "country_name": league.country.name,
                            "league_type": league.league_type,
                            "current_season_id": league.current_season_year,
                            "type": league.type,
                        }
                    )

                json_batch = json.dumps(batch_data, cls=DjangoJSONEncoder)[1:-1]
                if not first:
                    f.write(",")
                f.write(json_batch)

                processed += len(leagues)
                self.stdout.write(f"Processed {processed}/{total_leagues} leagues...")
                first = False

            f.write("]")

        self.stdout.write(
            self.style.SUCCESS(f"Exported {total_leagues} leagues to {output_file}")
        )
