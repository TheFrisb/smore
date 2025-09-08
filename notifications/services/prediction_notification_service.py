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
        for line in ticket.bet_lines.all():
            margin_bottom = "8px"

            lines.append(
                f'<p style="margin: 0;"><strong>{line.match.home_team.name}</strong> vs <strong>{line.match.away_team.name}</strong> - {line.bet} ({line.bet_type})</p>'
            )
            lines.append(
                f'<p style="margin: 0px 0px {margin_bottom} 0px;"><strong>Odds:</strong> {line.odds:.2f}</p>'
            )
        lines.append(
            f'<br><p style="margin: 0;"><strong>Total Odds:</strong> {ticket.total_odds:.2f}</p>'
        )
        if ticket.formatted_stake:
            lines.append(
                f'<p style="margin: 0;"><strong>Stake:</strong> {ticket.formatted_stake}%</p>'
            )
        return "".join(lines)

    def send_prediction_won_notification(self, prediction: Prediction):
        title = "Single Pick Status: WIN ✅"
        preview = f"{prediction.match.home_team} vs {prediction.match.away_team} - {prediction.prediction}"
        message = preview

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

    def _get_icon(self, sport_name: Product.Names):
        if sport_name == Product.Names.SOCCER:
            return NotificationRequest.IconNames.SOCCER
        elif sport_name == Product.Names.BASKETBALL:
            return NotificationRequest.IconNames.BASKETBALL

        return NotificationRequest.IconNames.TROPHY
