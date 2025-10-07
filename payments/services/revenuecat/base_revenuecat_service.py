from django.conf import settings


class BaseRevenuecatService:
    def __init__(self):
        self.api_key = settings.REVENUECAT_API_KEY
