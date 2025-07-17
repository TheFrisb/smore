import json
import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import SportLeague, SportCountry, Product

BATCH_SIZE = 2000


class Command(BaseCommand):
    help = 'Import sport leagues from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Input JSON file path')
        parser.add_argument('--media-root', type=str, default='',
                            help='Base media path for logo files')

    def handle(self, *args, **kwargs):
        input_file = kwargs['input_file']
        media_root = settings.MEDIA_ROOT

        # Preload countries
        countries = SportCountry.objects.values('id', 'name')
        country_map = {c['name']: c['id'] for c in countries}

        # Preload products
        product_ids = set()
        with open(input_file, 'r') as f:
            leagues_data = json.load(f)

        product_id = Product.objects.get(name=Product.Names.SOCCER).id

        total = len(leagues_data)
        self.stdout.write(f'Importing {total} leagues...')

        leagues_to_create = []
        for i, league in enumerate(leagues_data, 1):

            try:
                new_league = SportLeague(
                    external_id=league['external_id'],
                    name=league['name'],
                    product_id=product_id,
                    country_id=country_map[league['country_name']],
                    league_type=league['league_type'],
                    current_season_id=league['current_season_id'],
                    is_processed=league['is_processed'],
                    type=league['type']
                )

                # Handle logo file
                if league['logo']:
                    logo_path = os.path.join(media_root, league['logo'])
                    if os.path.exists(logo_path):
                        with open(logo_path, 'rb') as logo_file:
                            new_league.logo.save(
                                os.path.basename(league['logo']),
                                File(logo_file),
                                save=False
                            )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"League {league['name']}: Logo file {logo_path} not found"
                        ))

                leagues_to_create.append(new_league)
            except KeyError as e:
                self.stdout.write(self.style.WARNING(
                    f"League {league['name']}: Missing reference ({e})"
                ))

            # Batch commit
            if i % BATCH_SIZE == 0 or i == total:
                SportLeague.objects.bulk_create(
                    leagues_to_create,
                    batch_size=BATCH_SIZE
                )
                self.stdout.write(f'Imported {i}/{total} leagues...')
                leagues_to_create = []

        self.stdout.write(self.style.SUCCESS(f'Finished importing {len(leagues_to_create)} leagues'))
