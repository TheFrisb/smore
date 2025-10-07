from django.urls import path

from payments.mobile.views import (
    ConsumablePurchaseWebhookView,
    ConsumeConsumableView,
    SubscriptionWebhookView,
)

urlpatterns = [
    path("webhook/consumable/", ConsumablePurchaseWebhookView.as_view()),
    path("webhook/subscription/", SubscriptionWebhookView.as_view()),
    path("consumable/consume/", ConsumeConsumableView.as_view()),
]
