from django.urls import path

from accounts.api.views import CreateWithdrawalRequestView

urlpatterns = [
    path(
        "request-withdrawal/",
        CreateWithdrawalRequestView.as_view(),
        name="request_withdrawal",
    ),
]
