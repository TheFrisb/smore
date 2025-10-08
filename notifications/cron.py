# notifications/cron.py
import logging
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from core.models import Prediction, Ticket
from notifications.models import NotificationRequest, UserNotification
from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)
from subscriptions.models import Product

logger = logging.getLogger("cron")


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

    if product_name == Product.Names.SOCCER:
        # For soccer: only tickets matter
        filterable_list = [latest_ticket_time]
    else:
        # For others: predictions + tickets matter
        filterable_list = [latest_prediction_time, latest_ticket_time]

    latest_times = [t for t in filterable_list if t is not None]

    if not latest_times:
        return False

    latest_time = max(latest_times)

    if now - latest_time < timedelta(minutes=delay_minutes):
        return False

    if product_name == Product.Names.SOCCER:
        # Only care about newer tickets
        newer_activity = Ticket.objects.filter(
            product__name=product_name, created_at__gt=latest_time
        ).exists()
    else:
        # Care about both newer predictions and newer tickets
        newer_predictions = Prediction.objects.filter(
            product__name=product_name, created_at__gt=latest_time
        ).exists()
        newer_tickets = Ticket.objects.filter(
            product__name=product_name, created_at__gt=latest_time
        ).exists()
        newer_activity = newer_predictions or newer_tickets

    if newer_activity:
        return False

    prediction_notification_service = PredictionNotificationService()
    prediction_notification_service.send_daily_picks_notification(product_name)
    return True


def send_basketball_daily_picks_notification():
    current_date = timezone.now().date()
    formatted_date = current_date.strftime("%d.%m.%Y")

    title = f"Basketball selection for {formatted_date} is out!"
    return _send_daily_picks_notification(
        Product.Names.BASKETBALL, title, delay_minutes=30
    )


def send_soccer_daily_picks_notification():
    current_date = timezone.now().date()
    formatted_date = current_date.strftime("%d.%m.%Y")

    title = f"Soccer selection for {formatted_date} is out!"

    return _send_daily_picks_notification(
        Product.Names.SOCCER,
        title,
        delay_minutes=30,  # Changed from 1 second to 30 minutes for consistency
    )


def mark_notifications_as_not_important_for_product(product_name):
    now = timezone.now()
    today = now.date()

    predictions = Prediction.objects.filter(
        status=Prediction.Status.PENDING,
        match__kickoff_datetime__date=today,
        product__name=product_name,
    )

    tickets = Ticket.objects.filter(
        status=Ticket.Status.PENDING,
        starts_at__date=today,
        product__name=product_name,
    )

    start_times = [pred.match.kickoff_datetime for pred in predictions] + [
        ticket.starts_at for ticket in tickets if ticket.starts_at
    ]

    if not start_times:
        return

    max_start_time = max(start_times)

    if now >= max_start_time:
        prediction_notification_service = PredictionNotificationService()
        prediction_notification_service.mark_notifications_as_not_important(
            product_name, max_start_time
        )


def mark_soccer_notifications_as_not_important():
    mark_notifications_as_not_important_for_product(Product.Names.SOCCER)


def mark_basketball_notifications_as_not_important():
    mark_notifications_as_not_important_for_product(Product.Names.BASKETBALL)


def delete_older_notifications():
    today_date = timezone.now().date()
    older_than_three_days = today_date - timedelta(days=3)
    UserNotification.objects.filter(created_at__date__lt=older_than_three_days).update(
        is_visible=False
    )
