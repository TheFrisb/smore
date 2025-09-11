# signals.py in your predictions app
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import UserNotification
from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)
from .models import Prediction, Ticket, Product


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


def mark_important_notifications_as_unimportant_if_needed(instance):
    """
    Mark notifications as non-important when the last object per product is resolved
    """
    created_at = instance.created_at
    product_name = instance.product.name

    # Check if there are any pending predictions or tickets for this product and date
    pending_tickets = Ticket.objects.filter(
        product__name=product_name,
        status=Ticket.Status.PENDING,
        created_at__date=created_at.date()
    ).exists()

    pending_predictions = Prediction.objects.filter(
        product__name=product_name,
        status=Prediction.Status.PENDING,
        created_at__date=created_at.date()
    ).exists()

    if pending_tickets or pending_predictions:
        return

    # Map product names to notification titles
    title_map = {
        Product.Names.BASKETBALL: "Basketball daily picks are in!",
        Product.Names.SOCCER: "Soccer daily picks are in!",
    }

    title = title_map.get(product_name)
    if title:
        UserNotification.objects.filter(
            title=title,
            created_at__date=created_at.date(),
            is_important=True
        ).update(is_important=False)
