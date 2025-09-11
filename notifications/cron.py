# notifications/cron.py
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from core.models import Prediction, Ticket, Product
from notifications.models import NotificationRequest
from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)


def _send_daily_picks_notification(product_name, title, delay_minutes=30):
    now = timezone.now()
    today = now.date()

    if NotificationRequest.objects.filter(title=title, created_at__date=today).exists():
        return False

    latest_prediction_time = Prediction.objects.filter(
        product__name=product_name, created_at__date=today
    ).aggregate(Max("created_at"))["created_at__max"]

    latest_ticket_time = Ticket.objects.filter(
        product__name=product_name, created_at__date=today
    ).aggregate(Max("created_at"))["created_at__max"]

    latest_times = [
        t for t in [latest_prediction_time, latest_ticket_time] if t is not None
    ]
    if not latest_times:
        return False

    latest_time = max(latest_times)

    if now - latest_time < timedelta(minutes=delay_minutes):
        return False

    newer_predictions = Prediction.objects.filter(
        product__name=product_name, created_at__gt=latest_time
    ).exists()

    newer_tickets = Ticket.objects.filter(
        product__name=product_name, created_at__gt=latest_time
    ).exists()

    if newer_predictions or newer_tickets:
        return False

    prediction_notification_service = PredictionNotificationService()
    prediction_notification_service.send_daily_picks_notification(product_name)
    return True


def send_basketball_daily_picks_notification():
    return _send_daily_picks_notification(
        Product.Names.BASKETBALL, "Basketball daily picks are in!", delay_minutes=30
    )


def send_soccer_daily_picks_notification():
    return _send_daily_picks_notification(
        Product.Names.SOCCER,
        "Soccer daily picks are in!",
        delay_minutes=30,  # Changed from 1 second to 30 minutes for consistency
    )
