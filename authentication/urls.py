from django.urls import path

from .views import (
    GetMeView,
    LoginView,
    RefreshTokenView,
    RegisterUserView,
    PasswordResetView,
    AppleReceiverView,
    GoogleReceiverView, UpdateFCMTokenView,
)

app_name = "authentication"
urlpatterns = [
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("refresh-token/", RefreshTokenView.as_view(), name="token_refresh"),
    path("refresh", RefreshTokenView.as_view(), name="token_refresh_temp"),
    path("me/", GetMeView.as_view(), name="get_me"),
    path("me/update-fcm-token/", UpdateFCMTokenView.as_view(), name="update_fcm_token"),
    path("register/", RegisterUserView.as_view(), name="register_user"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("apple-receiver/", AppleReceiverView.as_view(), name="apple_receiver"),
    path("google-receiver/", GoogleReceiverView.as_view(), name="google_receiver"),
]
