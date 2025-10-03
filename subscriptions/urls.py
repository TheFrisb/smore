from django.urls import path

from subscriptions.views import PlansView

app_name = "subscriptions"
urlpatterns = [
    path("plans/", PlansView.as_view(), name="plans"),
]
