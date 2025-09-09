# signals.py in your predictions app
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import UserNotification
from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)
from .models import Prediction, Ticket


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
            prediction_notification_service = PredictionNotificationService()
            prediction_notification_service.send_prediction_won_notification(instance)

            mark_important_notifications_as_unimportant_if_needed(instance.created_at)


@receiver(post_save, sender=Ticket)
def handle_ticket_status_change(sender, instance, **kwargs):
    """
    Send notification when Ticket status changes from PENDING to WON
    """
    if instance.status == Ticket.Status.WON and instance.tracker.has_changed("status"):
        previous_status = instance.tracker.previous("status")
        if previous_status == Ticket.Status.PENDING:
            prediction_notification_service = PredictionNotificationService()
            prediction_notification_service.send_ticket_won_notification(instance)

            mark_important_notifications_as_unimportant_if_needed(instance.created_at)


def mark_important_notifications_as_unimportant_if_needed(created_at):
    tickets = Ticket.objects.filter(
        status=Ticket.Status.PENDING, created_at__date=created_at.date()
    )
    predictions = Prediction.objects.filter(
        status=Prediction.Status.PENDING, created_at__date=created_at.date()
    )

    if tickets.exists() or predictions.exists():
        return

    UserNotification.objects.filter(
        is_important=True, created_at__date=created_at.date()
    ).update(is_important=False)
