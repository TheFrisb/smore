from django.urls import path

from accounts.api.views import CreateWithdrawalRequestView, PostSendConfirmEmailMailView, DeleteMyAccountView

urlpatterns = [
    path(
        "request-withdrawal/",
        CreateWithdrawalRequestView.as_view(),
        name="request_withdrawal",
    ),
    path(
        "resend-email-confirmation/",
        PostSendConfirmEmailMailView.as_view(),
        name="resend_email_confirmation",
    ),
    path(
        "delete/",
        DeleteMyAccountView.as_view(),
        name="delete_my_account",
    )
]
