from django.urls import path

from .views import (
    HomeView,
    HistoryView,
    FaqView,
    HowToJoinView,
    AboutUsView,
    ContactUsView,
    DisclaimerView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiesPolicyView,
    UpcomingMatchesView,
    SubscriptionRequiredView,
    TelegramLandingView,
    DetailedPredictionView,
    AiAssistantView,
    ReferralTelegramLandingView,
    VerifyEmailView,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("history/", HistoryView.as_view(), name="history"),
    path("frequently-asked-questions/", FaqView.as_view(), name="faq"),
    path("how-to-join/", HowToJoinView.as_view(), name="how_to_join"),
    path("about-us/", AboutUsView.as_view(), name="about_us"),
    path("support/", ContactUsView.as_view(), name="contact_us"),
    path("disclaimer/", DisclaimerView.as_view(), name="disclaimer"),
    path("terms-of-service/", TermsOfServiceView.as_view(), name="terms_of_service"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("cookies-policy/", CookiesPolicyView.as_view(), name="cookies_policy"),
    path("upcoming-matches/", UpcomingMatchesView.as_view(), name="upcoming_matches"),
    path(
        "subscription-required/",
        SubscriptionRequiredView.as_view(),
        name="subscription_required",
    ),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path(
        "predictions/<int:pk>/",
        DetailedPredictionView.as_view(),
        name="detailed_prediction",
    ),
    path("ai-assistant/", AiAssistantView.as_view(), name="ai_assistant"),
    path("start/", TelegramLandingView.as_view(), name="telegram_landing"),
    path(
        "begin/", ReferralTelegramLandingView.as_view(), name="telegram_landing_begin"
    ),
]
