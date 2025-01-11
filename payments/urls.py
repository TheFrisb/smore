from django.urls import path

from payments.views import CreateCheckoutUrlView, stripe_webhook

urlpatterns = [
    path("checkout/", CreateCheckoutUrlView.as_view(), name="checkout"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]
