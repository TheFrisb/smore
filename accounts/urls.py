from django.urls import path

from .views import (
    LoginUserView,
    LogoutUserView,
    RegisterUserView,
    MyAccountView,
    MyNetworkView,
    ManagePlanView,
    RequestWithdrawalView,
    ContactUsView,
    FaqView,
    ReferralProgram,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordResetRequestSuccessView,
    VerifyEmailView,
    WithdrawalHistoryView,
)

app_name = "accounts"
urlpatterns = [
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout/", LogoutUserView.as_view(), name="logout"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("my-account/", MyAccountView.as_view(), name="my_account"),
    path("my-network/", MyNetworkView.as_view(), name="my_network"),
    path("manage-plan/", ManagePlanView.as_view(), name="manage_plan"),
    path(
        "request-withdrawal/",
        RequestWithdrawalView.as_view(),
        name="request_withdrawal",
    ),
    path("contact-us/", ContactUsView.as_view(), name="contact_us"),
    path("faq/", FaqView.as_view(), name="faq"),
    path("referral-program/", ReferralProgram.as_view(), name="referral_program"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-request-success/",
        PasswordResetRequestSuccessView.as_view(),
        name="password_reset_request_success",
    ),
    path(
        "verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify_email"
    ),
    path(
        "withdrawal-history/",
        WithdrawalHistoryView.as_view(),
        name="withdrawal_history",
    ),
]
