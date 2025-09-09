from datetime import timedelta

from django.utils import timezone

from core.models import Prediction, Product
from notifications.models import NotificationRequest
from notifications.services.prediction_notification_service import (
    PredictionNotificationService,
)


def send_daily_picks_notification():
    now = timezone.now()
    today = now.date()

    if NotificationRequest.objects.filter(
        title="Daily picks are in!", created_at__date=today
    ).exists():
        return

    time_threshold = now - timedelta(minutes=30)

    basketball_predictions = Prediction.objects.filter(
        product__name=Product.Names.BASKETBALL,
        created_at__date=today,
        created_at__lte=time_threshold,
    )

    if not basketball_predictions.exists():
        return

    prediction_notification_service = PredictionNotificationService()
    prediction_notification_service.send_daily_picks_notification()
