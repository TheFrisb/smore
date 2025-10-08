from django.urls import path

from payments.mobile.views import (
    ConsumablePurchaseWebhookView,
    ConsumeConsumableView,
    subscription_webhook_view,
)

urlpatterns = [
    path("webhook/consumable/", ConsumablePurchaseWebhookView.as_view()),
    path("webhook/subscription/", subscription_webhook_view),
    path("consumable/consume/", ConsumeConsumableView.as_view()),
]
