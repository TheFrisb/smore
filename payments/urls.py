from django.urls import path

from payments.views import (
    CreateSubscriptionCheckoutUrl,
    stripe_webhook,
    ManageSubscriptionView,
    UpdateSubscriptionView,
    SubscriptionPaymentSuccessView,
    CreatePredictionCheckoutUrl,
)

app_name = "payments"
urlpatterns = [
    path("checkout/", CreateSubscriptionCheckoutUrl.as_view(), name="checkout"),
    path(
        "prediction/checkout/<int:prediction_id>/",
        CreatePredictionCheckoutUrl.as_view(),
        name="prediction_checkout",
    ),
    path(
        "manage-subscription/",
        ManageSubscriptionView.as_view(),
        name="manage_subscription",
    ),
    path(
        "update-subscription/",
        UpdateSubscriptionView.as_view(),
        name="update_subscription",
    ),
    path(
        "payment-success/",
        SubscriptionPaymentSuccessView.as_view(),
        name="payment_success",
    ),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]
