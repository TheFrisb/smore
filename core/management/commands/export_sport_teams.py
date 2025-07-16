import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from core.models import SportTeam, ApiSportModel

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = 'Export sport teams to JSON file'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Output JSON file path')

    def handle(self, *args, **kwargs):
        output_file = kwargs['output_file']
        total_teams = SportTeam.objects.filter(type=ApiSportModel.SportType.SOCCER).count()
        processed = 0

        with open(output_file, 'w') as f:
            f.write('[')
            first = True

            while processed < total_teams:
                teams = SportTeam.objects.filter(type=ApiSportModel.SportType.SOCCER).select_related(
                    'product', 'league'
                ).only(
                    'external_id',
                    'name',
                    'logo',
                    'product__id',
                    'league__external_id',
                    'type'
                ).order_by('id')[processed:processed + BATCH_SIZE]

                batch_data = []
                for team in teams:
                    batch_data.append({
                        'external_id': team.external_id,
                        'name': team.name,
                        'logo': team.logo.name if team.logo else None,
                        'product_id': team.product_id,
                        'league_external_id': team.league.external_id,
                        'type': team.type
                    })

                json_batch = json.dumps(batch_data, cls=DjangoJSONEncoder)[1:-1]
                if not first:
                    f.write(',')
                f.write(json_batch)

                processed += len(teams)
                self.stdout.write(f'Processed {processed}/{total_teams} teams...')
                first = False

            f.write(']')

        self.stdout.write(self.style.SUCCESS(f'Exported {total_teams} teams to {output_file}'))
