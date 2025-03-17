from django.core.management.base import BaseCommand

from core.services.basketball_api_service import BasketballApiService


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        basketball_api_service = BasketballApiService()
        basketball_api_service.populate_upcoming_matches()
