import json
import os

from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import SportTeam, SportLeague, Product

BATCH_SIZE = 2000


class Command(BaseCommand):
    help = 'Import sport teams from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Input JSON file path')
        parser.add_argument('--media-root', type=str, default='',
                            help='Base media path for logo files')

    def handle(self, *args, **kwargs):
        input_file = kwargs['input_file']
        media_root = kwargs['media_root']

        # Preload leagues
        leagues = SportLeague.objects.values('id', 'external_id')
        league_map = {l['external_id']: l['id'] for l in leagues}

        with open(input_file, 'r') as f:
            teams_data = json.load(f)

        product_id = Product.objects.get(name=Product.Names.SOCCER).id
        total = len(teams_data)
        self.stdout.write(f'Importing {total} teams...')

        teams_to_create = []
        for i, team in enumerate(teams_data, 1):

            try:
                new_team = SportTeam(
                    external_id=team['external_id'],
                    name=team['name'],
                    product_id=product_id,
                    league_id=league_map[team['league_external_id']],
                    type=team['type']
                )

                # Handle logo file
                if team['logo']:
                    logo_path = os.path.join(media_root, team['logo'])
                    if os.path.exists(logo_path):
                        with open(logo_path, 'rb') as logo_file:
                            new_team.logo.save(
                                os.path.basename(team['logo']),
                                File(logo_file),
                                save=False
                            )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Team {team['name']}: Logo file {logo_path} not found"
                        ))

                teams_to_create.append(new_team)
            except KeyError as e:
                self.stdout.write(self.style.WARNING(
                    f"Team {team['name']}: Missing reference ({e})"
                ))

            # Batch commit
            if i % BATCH_SIZE == 0 or i == total:
                SportTeam.objects.bulk_create(
                    teams_to_create,
                    batch_size=BATCH_SIZE
                )
                self.stdout.write(f'Imported {i}/{total} teams...')
                teams_to_create = []

        self.stdout.write(self.style.SUCCESS(f'Finished importing {len(teams_to_create)} teams'))
