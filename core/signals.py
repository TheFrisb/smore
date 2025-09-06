# signals.py in your predictions app
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import NotificationRequest, NotificationTopic
from .models import Prediction, Ticket, BetLine, Product


@receiver(post_save, sender=Prediction)
def handle_prediction_status_change(sender, instance, **kwargs):
    """
    Send notification when Prediction status changes from PENDING to WON
    """
    if instance.status == Prediction.Status.WON and instance.tracker.has_changed(
            "status"
    ):
        previous_status = instance.tracker.previous("status")
        if previous_status == Prediction.Status.PENDING:
            # Get or create ALL topic
            topic, _ = NotificationTopic.objects.get_or_create(name="ALL")

            # Create notification message
            sport_name = instance.product.name
            title = f"{sport_name} prediction won!"
            preview = f"{instance.match.home_team.name} vs {instance.match.away_team.name}: {instance.prediction}"
            message = f"{instance.match.home_team.name} vs {instance.match.away_team.name}: {instance.prediction}"

            # Set appropriate icon based on sport
            if sport_name == Product.Names.SOCCER:
                icon = NotificationRequest.IconNames.SOCCER
            elif sport_name == Product.Names.BASKETBALL:
                icon = NotificationRequest.IconNames.BASKETBALL
            else:
                icon = NotificationRequest.IconNames.TROPHY  # Default icon

            NotificationRequest.objects.create(
                topic=topic,
                title=title,
                preview=preview,
                message=message,
                icon=icon,
                is_important=False,
            )


@receiver(post_save, sender=Ticket)
def handle_ticket_status_change(sender, instance, **kwargs):
    """
    Send notification when Ticket status changes from PENDING to WON
    """
    if instance.status == Ticket.Status.WON and instance.tracker.has_changed("status"):
        previous_status = instance.tracker.previous("status")
        if previous_status == Ticket.Status.PENDING:
            # Get or create ALL topic
            topic, _ = NotificationTopic.objects.get_or_create(name="ALL")

            # Count won bet lines
            won_count = instance.bet_lines.filter(status=BetLine.Status.WON).count()
            total_count = instance.bet_lines.count()

            # Create notification message
            sport_name = instance.product.name
            title = f"{sport_name} ticket won!"
            preview = f"{won_count}/{total_count} bets won"
            message = f"{won_count}/{total_count} bets won"

            # Set appropriate icon based on sport
            if sport_name == Product.Names.SOCCER:
                icon = NotificationRequest.IconNames.SOCCER
            elif sport_name == Product.Names.BASKETBALL:
                icon = NotificationRequest.IconNames.BASKETBALL
            else:
                icon = NotificationRequest.IconNames.TROPHY  # Default icon

            NotificationRequest.objects.create(
                topic=topic,
                title=title,
                preview=preview,
                message=message,
                icon=icon,
                is_important=False,
            )
