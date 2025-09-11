from django.utils import timezone

from core.models import Ticket, Prediction, Product
from notifications.models import NotificationRequest, NotificationTopic
from notifications.services.fcm_service import FCMService


class PredictionNotificationService:
    def __init__(self):
        self.fcm_service = FCMService()

    def send_ticket_won_notification(self, ticket: Ticket):
        first_bet_line = ticket.bet_lines.first()

        title = "Parlay Status: WIN ✅"
        preview = f"{self._get_emoji(ticket.product.name)} {first_bet_line.match.home_team} vs {first_bet_line.match.away_team} - {first_bet_line.bet} ({first_bet_line.bet_type})"
        message = self._build_ticket_message(ticket)

        topic = self.get_default_topic()
        icon = self._get_icon(ticket.product.name)

        NotificationRequest.objects.create(
            topic=topic,
            title=title,
            preview=preview,
            message=message,
            icon=icon,
            is_important=False,
        )

    def _build_ticket_message(self, ticket: Ticket) -> str:
        lines = []
        bet_lines = ticket.bet_lines.all()

        for i, line in enumerate(bet_lines):
            lines.append(
                f"<p><strong>{self._get_emoji(ticket.product.name)} {line.match.home_team.name}</strong> vs <strong>{line.match.away_team.name}</strong> - {line.bet} ({line.bet_type})</p>"
            )

        return "".join(lines)

    def send_prediction_won_notification(self, prediction: Prediction):
        title = "Single Pick: WIN ✅"
        preview = f"{self._get_emoji(prediction.product.name)} {prediction.match.home_team} vs {prediction.match.away_team} - {prediction.prediction}"
        message = f"<strong>{self._get_emoji(prediction.product.name)} {prediction.match.home_team}</strong> vs <strong>{prediction.match.away_team}</strong> - {prediction.prediction}"

        topic = self.get_default_topic()
        icon = self._get_icon(prediction.product.name)

        NotificationRequest.objects.create(
            topic=topic,
            title=title,
            preview=preview,
            message=message,
            icon=icon,
            is_important=False,
        )

    def get_default_topic(self) -> NotificationTopic:
        topic, created = NotificationTopic.objects.get_or_create(name="ALL")
        return topic

    def get_topic(self, product_name: Product.Names) -> NotificationTopic:
        topic, created = NotificationTopic.objects.get_or_create(
            name=product_name.upper()
        )

        return topic

    def _get_icon(self, sport_name: Product.Names):
        if sport_name == Product.Names.SOCCER:
            return NotificationRequest.IconNames.SOCCER
        elif sport_name == Product.Names.BASKETBALL:
            return NotificationRequest.IconNames.BASKETBALL

        return NotificationRequest.IconNames.TROPHY

    def send_daily_picks_notification(self, product_name: Product.Names):
        # Convert product name to sentence case for the title
        title = f"{product_name.capitalize()} daily picks are in!"
        preview = "Tap to see today's top picks"
        message = self._build_daily_picks_message(product_name)

        topic = self.get_topic(product_name)
        icon = NotificationRequest.IconNames.TROPHY

        NotificationRequest.objects.create(
            topic=topic,
            title=title,
            preview=preview,
            message=message,
            icon=icon,
            is_important=True,
        )

    def _build_daily_picks_message(self, product_name: Product.Names) -> str:
        today = timezone.now().date()
        lines = []

        # Get all predictions for today for this product
        predictions = Prediction.objects.filter(
            created_at__date=today,
            status=Prediction.Status.PENDING,
            product__name=product_name,
        ).select_related(
            "match", "match__home_team", "match__away_team", "match__league", "product"
        )

        # Get all tickets for today for this product
        tickets = Ticket.objects.filter(
            created_at__date=today,
            status=Ticket.Status.PENDING,
            product__name=product_name,
        ).prefetch_related(
            "bet_lines",
            "bet_lines__match",
            "bet_lines__match__home_team",
            "bet_lines__match__away_team",
            "bet_lines__match__league",
        )

        # Count single picks and tickets
        single_pick_count = predictions.count()
        ticket_count = tickets.count()

        parlay_label = "Premium Parlay" if ticket_count == 1 else "Premium Parlays"
        single_label = "match" if single_pick_count == 1 else "matches"

        # Get emoji for the product
        emoji = self._get_emoji(product_name)

        # Start with the intro sentence
        lines.append(
            f"<p>We've got {single_pick_count} {single_label} and {ticket_count} {parlay_label} prepared for today.</p>"
        )

        # List all single picks with emoji
        if single_pick_count > 0:
            for prediction in predictions:
                lines.append(
                    f"<p><strong>{emoji} {prediction.match.home_team.name}</strong> vs <strong>{prediction.match.away_team.name}</strong><p>"
                )

        return "".join(lines)

    def _get_emoji(self, product_name: Product.Names):
        emoji_map = {
            Product.Names.SOCCER: "⚽",
            Product.Names.BASKETBALL: "🏀",
            Product.Names.NFL_NHL: "🏈",  # Default to football for NFL/NHL
            Product.Names.TENNIS: "🎾",
            Product.Names.AI_ANALYST: "🤖",  # Default for AI Analyst
        }
        return emoji_map.get(product_name, "🎯")  # Default emoji if not found
