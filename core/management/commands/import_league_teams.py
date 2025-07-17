import json

from django.core.management.base import BaseCommand

from core.models import SportLeagueTeam, SportLeague, SportTeam

BATCH_SIZE = 2000


class Command(BaseCommand):
    help = 'Import SportLeagueTeam relationships from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Input JSON file path')

    def handle(self, *args, **kwargs):
        input_file = kwargs['input_file']

        # Preload lookup mappings
        leagues = SportLeague.objects.values('id', 'external_id', 'type')
        teams = SportTeam.objects.values('id', 'external_id', 'type')

        league_map = {(l['external_id'], l['type']): l['id'] for l in leagues}
        team_map = {(t['external_id'], t['type']): t['id'] for t in teams}

        with open(input_file, 'r') as f:
            relationships_data = json.load(f)

        total = len(relationships_data)
        self.stdout.write(f'Importing {total} league-team relationships...')

        relationships_to_create = []
        for i, rel in enumerate(relationships_data, 1):
            try:
                league_id = league_map[(rel['league_external_id'], rel['league_type'])]
                team_id = team_map[(rel['team_external_id'], rel['team_type'])]

                relationships_to_create.append(SportLeagueTeam(
                    league_id=league_id,
                    team_id=team_id,
                    season=rel['season']
                ))
            except KeyError as e:
                self.stdout.write(self.style.WARNING(
                    f"Missing reference for relationship: {rel} ({e})"
                ))

            # Batch commit
            if i % BATCH_SIZE == 0 or i == total:
                SportLeagueTeam.objects.bulk_create(
                    relationships_to_create,
                    batch_size=BATCH_SIZE,
                    ignore_conflicts=True
                )
                self.stdout.write(f'Imported {i}/{total} relationships...')
                relationships_to_create = []

        self.stdout.write(self.style.SUCCESS(
            f'Finished importing {total} league-team relationships'
        ))
