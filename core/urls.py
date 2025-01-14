from django.urls import path

from .views import (
    HomeView,
    HistoryView,
    PlansView,
    FaqView,
    HowToJoinView,
    AboutUsView,
    ContactUsView,
    DisclaimerView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiesPolicyView,
)

app_name = "core"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("history/", HistoryView.as_view(), name="history"),
    path("plans/", PlansView.as_view(), name="plans"),
    path("frequently-asked-questions/", FaqView.as_view(), name="faq"),
    path("how-to-join/", HowToJoinView.as_view(), name="how_to_join"),
    path("about-us/", AboutUsView.as_view(), name="about_us"),
    path("support/", ContactUsView.as_view(), name="contact_us"),
    path("disclaimer/", DisclaimerView.as_view(), name="disclaimer"),
    path("terms-of-service/", TermsOfServiceView.as_view(), name="terms_of_service"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("cookies-policy/", CookiesPolicyView.as_view(), name="cookies_policy"),
]
