from django.core.management.base import BaseCommand

from core.models import SportLeague
from core.services.basketball_api_service import BASKETBALL_NCAA_LEAGUE_IDS
from subscriptions.models import Product


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    #
    # def handle(self, *args, **kwargs):
    #     sport_api_service = SportApiService()
    #
    #     self.load_matches()
    #
    # def load_matches(self):
    #     start_date = datetime(2025, 3, 1, tzinfo=timezone.utc)
    #     end_date = datetime(2025, 4, 13, tzinfo=timezone.utc)
    #
    #     football_api_service = FootballApiService()
    #     basketball_api_service = BasketballApiService()
    #
    #     # basketball_api_service.populate_matches(start_date, end_date)
    #     football_api_service.populate_matches(start_date, end_date)

    def handle(self, *args, **kwargs):
        leagues = SportLeague.objects.filter(external_id__in=BASKETBALL_NCAA_LEAGUE_IDS)

        for league in leagues:
            print(
                f"League product name: {league.product.name} - League type: {league.type} - League name: {league.name}"
            )

            if league.type == SportLeague.SportType.BASKETBALL:
                print(f"Updating the league's product to BASKETBALL")
                league.product = Product.objects.get(name=Product.Names.BASKETBALL)
                league.save()
            elif (
                league.type == SportLeague.SportType.NHL
                or league.type == SportLeague.SportType.NFL
            ):
                print(f"Updating the league's product to NHL_NFL")
                league.product = Product.objects.get(name=Product.Names.NFL_NHL)
                league.save()

            elif league.type == SportLeague.SportType.SOCCER:
                print(f"Updating the league's product to SOCCER")
                league.product = Product.objects.get(name=Product.Names.SOCCER)
                league.save()

            print(
                f"League product name: {league.product.name} - League type: {league.type} - League name: {league.name}"
            )
