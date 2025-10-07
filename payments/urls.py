from django.urls import include, path

from payments.nviews import (
    CreateDailyOfferCheckoutUrl,
    CreatePredictionCheckoutUrl,
    CreateTicketCheckoutUrl,
    ManageSubscriptionView,
    PurchasePaymentSuccessView,
    SubscriptionPaymentSuccessView,
    VerifyMobilePurchaseView,
)
from payments.views.checkout import (
    CreateSubscriptionCheckoutUrl,
    UpdateSubscriptionView,
)
from payments.views.stripe_webhook import stripe_webhook

app_name = "payments"
urlpatterns = [
    path("checkout/", CreateSubscriptionCheckoutUrl.as_view(), name="checkout"),
    path(
        "prediction/checkout/<int:prediction_id>/",
        CreatePredictionCheckoutUrl.as_view(),
        name="prediction_checkout",
    ),
    path(
        "daily-offer/checkout/",
        CreateDailyOfferCheckoutUrl.as_view(),
        name="daily_offer_checkout",
    ),
    path(
        "ticket/checkout/<int:ticket_id>/",
        CreateTicketCheckoutUrl.as_view(),
        name="ticket_checkout",
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
    path(
        "payment/prediction/success/<int:prediction_pk>/",
        PurchasePaymentSuccessView.as_view(),
        name="purchase_payment_success",
    ),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    path(
        "mobile/verify-purchase/",
        VerifyMobilePurchaseView.as_view(),
        name="verify_mobile_purchase",
    ),
    path("revenuecat/", include("payments.mobile.urls")),
]
