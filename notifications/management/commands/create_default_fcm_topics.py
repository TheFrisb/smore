from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate 100 random predictions with status WON or LOST."

    def handle(self, *args, **options):
        topics = ["ALL"]

        for topic in topics:
            from notifications.models import NotificationTopic

            NotificationTopic.objects.get_or_create(name=topic)
