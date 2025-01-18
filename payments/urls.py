from django.urls import path

from payments.views import (
    CreateCheckoutUrlView,
    stripe_webhook,
    ManageSubscriptionView,
    UpdateSubscriptionView,
    PaymentSuccessView,
)

app_name = "payments"
urlpatterns = [
    path("checkout/", CreateCheckoutUrlView.as_view(), name="checkout"),
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
    path("payment-success/", PaymentSuccessView.as_view(), name="payment_success"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]
