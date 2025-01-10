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
]
