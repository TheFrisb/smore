from django.core.management.base import BaseCommand

from core.models import SportMatch, Product
from core.services.basketball_api_service import BasketballApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        basketball_api_service = BasketballApiService()
        SportMatch.objects.filter(product=Product.objects.get(name=Product.Names.BASKETBALL)).delete()

        basketball_api_service.populate_upcoming_matches()
