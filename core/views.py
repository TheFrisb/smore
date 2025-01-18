import logging
from datetime import date
from itertools import groupby

from django.urls import reverse
from django.views.generic import TemplateView

from accounts.views import BaseAccountView
from core.models import (
    Product,
    Addon,
    PickOfTheDay,
    Prediction,
    FrequentlyAskedQuestion,
)

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pick_of_the_day"] = PickOfTheDay.get_solo()
        context["page_title"] = "Home"
        context.update(self.get_button_context())

        return context

    def get_button_context(self):
        """
        Determine button text and URL based on user's login and subscription status.
        """
        user = self.request.user
        if not user.is_authenticated:
            return {
                "primary_button_text": "Get Started",
                "primary_button_url": reverse("accounts:register"),
            }

        user_subscription = getattr(user, "subscription", None)
        if user_subscription and user_subscription.is_active:
            return {
                "primary_button_text": "What's New",
                "primary_button_url": reverse("core:upcoming_matches"),
                "primary_button_description": "View upcoming matches",
            }

        return {
            "primary_button_text": "View Plans",
            "primary_button_url": reverse("core:plans"),
            "primary_button_description": "Choose a plan and get instant access to expert predictions",
        }

    def dispatch(self, request, *args, **kwargs):
        referral_code = request.GET.get("ref", None)
        if referral_code:
            logger.info(f"Home page visited with referral code: {referral_code}")
            request.session["referral_code"] = referral_code

        return super().dispatch(request, *args, **kwargs)


class HistoryView(TemplateView):
    template_name = "core/pages/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["predictions"] = self.get_history_predictions()
        context["page_title"] = "History"
        return context

    def get_history_predictions(self):
        predictions = Prediction.objects.filter(
            kickoff_date__lt=date.today(),
            visibility=Prediction.Visibility.PUBLIC,
            status__in=[Prediction.Status.WON, Prediction.Status.LOST],
        ).order_by("-kickoff_date", "-kickoff_time")

        return predictions


class PlansView(TemplateView):
    template_name = "core/pages/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()
        context["addons"] = Addon.objects.all().order_by("order")
        context["page_title"] = "Plans"

        return context


class FaqView(TemplateView):
    template_name = "core/pages/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["faq"] = FrequentlyAskedQuestion.objects.all().order_by("order")
        context["page_title"] = "FAQ"

        return context


class HowToJoinView(TemplateView):
    template_name = "core/pages/how_to_join.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "How to Join"
        return context


class AboutUsView(TemplateView):
    template_name = "core/pages/about_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "About Us"
        return context


class ContactUsView(TemplateView):
    template_name = "core/pages/contact_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Support"
        return context


class TermsOfServiceView(TemplateView):
    template_name = "core/pages/terms_of_service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Terms of Service"
        return context


class PrivacyPolicyView(TemplateView):
    template_name = "core/pages/privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Privacy Policy"
        return context


class DisclaimerView(TemplateView):
    template_name = "core/pages/disclaimer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Disclaimer"
        return context


class CookiesPolicyView(TemplateView):
    template_name = "core/pages/cookies_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cookies Policy"
        return context


class UpcomingMatchesView(BaseAccountView, TemplateView):
    template_name = "core/pages/upcoming_matches.html"

    def get_context_data(self, **kwargs):
        super().get_context_data(**kwargs)
        context = {"grouped_predictions": self.get_grouped_predictions()}
        context["pick_of_the_day"] = PickOfTheDay.get_solo()
        context["page_title"] = "Upcoming Matches"
        return context

    def get_grouped_predictions(self):
        predictions = Prediction.objects.filter(
            kickoff_date__gte=date.today(),
            visibility=Prediction.Visibility.PUBLIC,
            status=Prediction.Status.PENDING,
        ).order_by("kickoff_date", "kickoff_time")

        grouped_predictions = {
            kickoff_date: list(predictions)
            for kickoff_date, predictions in groupby(
                predictions, key=lambda x: x.kickoff_date
            )
        }

        return grouped_predictions


class SubscriptionRequiredView(TemplateView):
    template_name = "core/pages/subscription_required.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Subscription Required"
        return context
