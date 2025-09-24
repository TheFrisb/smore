# signals.py in your predictions app
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)
from .models import Prediction, Ticket


@receiver(post_save, sender=Prediction)
def handle_prediction_status_change(sender, instance, **kwargs):
    """
    Send notification when Prediction status changes from PENDING to WON or LOST
    """
    if instance.tracker.has_changed("status"):
        previous_status = instance.tracker.previous("status")
        if previous_status == Prediction.Status.PENDING:
            prediction_notification_service = PredictionNotificationService()
            if instance.status == Prediction.Status.WON:
                prediction_notification_service.send_prediction_won_notification(
                    instance
                )
            elif instance.status == Prediction.Status.LOST:
                prediction_notification_service.send_prediction_lost_notification(
                    instance
                )


@receiver(post_save, sender=Ticket)
def handle_ticket_status_change(sender, instance, **kwargs):
    """
    Send notification when Ticket status changes from PENDING to WON or LOST
    """
    if instance.tracker.has_changed("status"):
        previous_status = instance.tracker.previous("status")
        if previous_status == Ticket.Status.PENDING:
            prediction_notification_service = PredictionNotificationService()
            if instance.status == Ticket.Status.WON:
                prediction_notification_service.send_ticket_won_notification(instance)
            elif instance.status == Ticket.Status.LOST:
                prediction_notification_service.send_ticket_lost_notification(instance)
