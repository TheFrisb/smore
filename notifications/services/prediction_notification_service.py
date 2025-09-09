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
        preview = f"{first_bet_line.match.home_team} vs {first_bet_line.match.away_team} - {first_bet_line.bet} ({first_bet_line.bet_type})"
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
            # Add margin bottom to all lines except the last one
            margin_bottom = "0px"

            lines.append(
                f'<p style="margin: 0 0 {margin_bottom} 0;"><strong>Match:</strong> <strong>{line.match.home_team.name}</strong> vs <strong>{line.match.away_team.name}</strong></p>'
            )
            lines.append(
                f'<p style="margin: 0 0 {margin_bottom} 0;"><strong>League:</strong> {line.match.league.name}</p>'
            )
            lines.append(
                f'<p style="margin: 0 0 {margin_bottom} 0;"><strong>Bet:</strong> {line.bet} ({line.bet_type})</p>'
            )
            lines.append(
                f'<p style="margin: 0 0 {margin_bottom} 0;"><strong>Odds:</strong> {line.odds:.2f}</p>'
            )
            lines.append(
                f'<p style="margin: 0 0 {margin_bottom} 0;"><strong>Status:</strong> WON ✅</p>'
            )

            lines.append(
                f'<hr style="margin: 8px 0; border: 0; border-top: 0.5px solid #36bffa;">'
            )

        # Add total odds and stake
        lines.append("<br>")
        lines.append(
            f'<p style="margin: 0;"><strong>Total Odds:</strong> {ticket.total_odds:.2f}</p>'
        )

        if ticket.formatted_stake:
            lines.append(
                f'<p style="margin: 0;"><strong>Stake:</strong> {ticket.formatted_stake}%</p>'
            )

        return "".join(lines)

    def send_prediction_won_notification(self, prediction: Prediction):
        title = "Single Pick Status: WIN ✅"
        preview = f"{prediction.match.home_team} vs {prediction.match.away_team} - {prediction.prediction}"
        message = self._build_prediction_message(prediction)

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

    def _build_prediction_message(self, prediction: Prediction) -> str:
        lines = []

        lines.append(
            f'<p style="margin: 0 0 0 0;"><strong>Match:</strong> {prediction.match.home_team.name} vs {prediction.match.away_team.name}</p>'
        )
        lines.append(
            f'<p style="margin: 0 0 0 0;"><strong>League:</strong> {prediction.match.league.name}</p>'
        )
        lines.append(
            f'<p style="margin: 0 0 0 0;"><strong>Prediction:</strong> {prediction.prediction}</p>'
        )
        lines.append(
            f'<p style="margin: 0 0 0 0;"><strong>Odds:</strong> {prediction.odds:.2f}</p>'
        )
        lines.append(f'<p style="margin: 0;"><strong>Status:</strong> WON ✅</p>')

        return "".join(lines)

    def get_default_topic(self) -> NotificationTopic:
        topic, created = NotificationTopic.objects.get_or_create(name="ALL")
        return topic

    def _get_icon(self, sport_name: Product.Names):
        if sport_name == Product.Names.SOCCER:
            return NotificationRequest.IconNames.SOCCER
        elif sport_name == Product.Names.BASKETBALL:
            return NotificationRequest.IconNames.BASKETBALL

        return NotificationRequest.IconNames.TROPHY

    def send_daily_picks_notification(self):
        title = "Daily picks are in!"
        preview = "Tap to see today's top picks"
        message = self._build_daily_picks_message()

        topic = self.get_default_topic()
        icon = NotificationRequest.IconNames.TROPHY

        NotificationRequest.objects.create(
            topic=topic,
            title=title,
            preview=preview,
            message=message,
            icon=icon,
            is_important=True,
        )

    def _build_daily_picks_message(self) -> str:
        today = timezone.now().date()
        lines = []

        # Get all predictions for today
        predictions = Prediction.objects.filter(
            created_at__date=today, status=Prediction.Status.PENDING
        ).select_related(
            "match", "match__home_team", "match__away_team", "match__league", "product"
        )

        # Get all tickets for today
        tickets = Ticket.objects.filter(
            created_at__date=today, status=Ticket.Status.PENDING
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

        # Start with the intro sentence
        lines.append(
            f'<p style="margin-bottom: 8px">We\'ve got {single_pick_count} {single_label} and {ticket_count} {parlay_label} prepared for today.'
        )

        # List all single picks
        if single_pick_count > 0:
            for prediction in predictions:
                lines.append(
                    f"<p><strong>{prediction.match.home_team.name}</strong> vs <strong>{prediction.match.away_team.name}</strong><br></p>"
                )

        return "".join(lines)
