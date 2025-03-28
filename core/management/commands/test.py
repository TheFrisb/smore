from django.core.management.base import BaseCommand

from core.models import SportTeam, Product, ApiSportModel


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        sport_teams = SportTeam.objects.all()
        soccer = Product.objects.get(name=Product.Names.SOCCER)
        basketball = Product.objects.get(name=Product.Names.BASKETBALL)

        for team in sport_teams:
            if team.league.product != team.product:
                print(f"Team {team.name} has different product ({team.product}) than league's: {team.league.product}")
                team.product = team.league.product

                if team.league.product == soccer:
                    team.type = ApiSportModel.SportType.SOCCER
                elif team.league.product == basketball:
                    team.type = ApiSportModel.SportType.BASKETBALL

                team.save()
