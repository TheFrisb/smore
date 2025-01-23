import random
from datetime import timedelta, time

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from core.models import Prediction, Product


class Command(BaseCommand):
    help = "Generate 100 random predictions with status WON or LOST."

    def handle(self, *args, **options):
        # Get or create a default product (adjust if you have multiple products)
        product = Product.objects.get(name="Soccer")

        # List of sample teams and leagues
        teams = ["Team A", "Team B", "Team C", "Team D", "Team E", "Team F"]
        leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]

        # Start creating predictions
        predictions = []
        today = now().date()
        for i in range(100):
            home_team = random.choice(teams)
            away_team = random.choice([team for team in teams if team != home_team])
            kickoff_date = today + timedelta(days=random.randint(0, 30))
            kickoff_time = time(
                hour=random.randint(12, 22), minute=random.choice([0, 15, 30, 45])
            )
            status = random.choice([Prediction.Status.WON, Prediction.Status.LOST])
            visibility = Prediction.Visibility.PUBLIC
            odds = round(random.uniform(1.5, 5.0), 2)
            result = f"{random.randint(0, 5)}-{random.randint(0, 5)}"
            league = random.choice(leagues)

            predictions.append(
                Prediction(
                    product=product,
                    visibility=visibility,
                    home_team=home_team,
                    away_team=away_team,
                    prediction=f"Predicted win for {home_team}",
                    odds=odds,
                    result=result,
                    kickoff_date=kickoff_date,
                    kickoff_time=kickoff_time,
                    league=league,
                    status=status,
                )
            )

        # Bulk create predictions
        Prediction.objects.bulk_create(predictions)

        self.stdout.write(self.style.SUCCESS("Successfully created 100 predictions."))
