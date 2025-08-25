from django.urls import path

from .views import (
    GetMeView,
    LoginView,
    RefreshTokenView,
    RegisterUserView,
    PasswordResetView,
    AppleReceiverView,
    GoogleReceiverView,
)

app_name = "authentication"
urlpatterns = [
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("refresh-token/", RefreshTokenView.as_view(), name="token_refresh"),
    path("me/", GetMeView.as_view(), name="get_me"),
    path("register/", RegisterUserView.as_view(), name="register_user"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("apple-receiver/", AppleReceiverView.as_view(), name="apple_receiver"),
    path("google-receiver/", GoogleReceiverView.as_view(), name="google_receiver"),
]
