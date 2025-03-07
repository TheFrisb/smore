import logging
from itertools import groupby

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, DetailView

from accounts.models import PurchasedPredictions
from core.models import (
    Product,
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
        context["page_title"] = _("Home")
        context["show_ai_button"] = True
        context.update(self.get_button_context())

        return context

    def get_button_context(self):
        """
        Determine button text and URL based on user's login and subscription status.
        """
        user = self.request.user
        if not user.is_authenticated:
            return {
                "primary_button_text": _("Get Started"),
                "primary_button_url": reverse("accounts:register"),
            }

        user_subscription = getattr(user, "subscription", None)
        if user_subscription and user_subscription.is_active:
            return {
                "primary_button_text": _("Upcoming matches"),
                "primary_button_url": reverse("core:upcoming_matches"),
                "primary_button_description": _("View upcoming matches"),
            }

        return {
            "primary_button_text": _("View Plans"),
            "primary_button_url": reverse("core:plans"),
            "primary_button_description": _(
                "Choose a plan and get instant access to expert predictions"
            ),
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
        context["page_title"] = _("History")
        context["show_predictions"] = True
        return context

    def get_history_predictions(self):
        predictions = Prediction.objects.filter(
            visibility=Prediction.Visibility.PUBLIC,
            status__in=[Prediction.Status.WON, Prediction.Status.LOST],
        ).order_by("-match__kickoff_datetime")[0:20]

        return predictions


class DetailedPredictionView(DetailView):
    model = Prediction
    template_name = "core/pages/detail_prediction.html"
    context_object_name = "prediction"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "match",
                "match__home_team",
                "match__away_team",
                "match__league",
                "match__league__country",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Prediction Details")
        context["can_view_prediction"] = self.can_view_prediction()
        return context

    def can_view_prediction(self):
        prediction = self.get_object()

        if prediction.status != Prediction.Status.PENDING:
            return True

        if (
                self.request.user.is_authenticated
                and self.request.user.has_access_to_product(prediction.product)
        ):
            return True

        if (
                self.request.user.is_authenticated
                and PurchasedPredictions.objects.filter(
            user=self.request.user, prediction=prediction
        ).exists()
        ):
            return True

        return False

    def dispatch(self, request, *args, **kwargs):
        prediction = self.get_object()

        if (
                prediction.status != Prediction.Status.PENDING
                or not prediction.has_detailed_analysis
        ):
            logger.info(
                f"User {request.user} tried to access detailed prediction view for prediction {prediction.id} with status {prediction.status} and has_detailed_analysis {prediction.has_detailed_analysis}. Redirecting to home page."
            )
            return redirect("core:home")

        return super().dispatch(request, *args, **kwargs)


class PlansView(TemplateView):
    template_name = "core/pages/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscriptions"] = Product.objects.filter(
            type=Product.Types.SUBSCRIPTION
        ).order_by("order")
        context["addons"] = Product.objects.filter(type=Product.Types.ADDON).order_by(
            "order"
        )
        context["page_title"] = _("Plans")

        return context


class TelegramLandingView(TemplateView):
    template_name = "core/pages/telegram_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Free Telegram Channel")
        return context


class FaqView(TemplateView):
    template_name = "core/pages/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["faq"] = FrequentlyAskedQuestion.objects.all().order_by("order")
        context["page_title"] = _("FAQ")

        return context


class HowToJoinView(TemplateView):
    template_name = "core/pages/how_to_join.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("How to Join")
        return context


class AboutUsView(TemplateView):
    template_name = "core/pages/about_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("About Us")
        return context


class ContactUsView(TemplateView):
    template_name = "core/pages/contact_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Support")
        return context


class TermsOfServiceView(TemplateView):
    template_name = "core/pages/terms_of_service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Terms of Service")
        return context


class PrivacyPolicyView(TemplateView):
    template_name = "core/pages/privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Privacy Policy")
        return context


class DisclaimerView(TemplateView):
    template_name = "core/pages/disclaimer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Disclaimer")
        return context


class CookiesPolicyView(TemplateView):
    template_name = "core/pages/cookies_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Cookies Policy")
        return context


class UpcomingMatchesView(TemplateView):
    template_name = "core/pages/upcoming_matches.html"

    def get_context_data(self, **kwargs):
        super().get_context_data(**kwargs)
        context = {"grouped_predictions": self.get_grouped_predictions()}
        context["pick_of_the_day"] = PickOfTheDay.get_solo()
        context["page_title"] = _("Upcoming Matches")
        context["show_predictions"] = self.get_show_predictions()
        context["purchased_prediction_ids"] = self.get_purchased_prediction_ids()
        return context

    def get_purchased_prediction_ids(self):
        if not self.request.user.is_authenticated:
            return []

        return PurchasedPredictions.objects.filter(user=self.request.user).values_list(
            "prediction_id", flat=True
        )

    def get_grouped_predictions(self):
        predictions = (
            Prediction.objects.filter(
                match__kickoff_datetime__date__gte=timezone.now().date(),
                visibility=Prediction.Visibility.PUBLIC,
                status=Prediction.Status.PENDING,
            )
            .select_related(
                "match", "match__home_team", "match__away_team", "match__league"
            )
            .order_by("match__kickoff_datetime")
        )

        grouped_predictions = {
            kickoff_date: list(predictions)
            for kickoff_date, predictions in groupby(
                predictions, key=lambda p: p.match.kickoff_datetime.date()
            )
        }

        return grouped_predictions

    def get_show_predictions(self):
        soccer = Product.objects.get(name="Soccer")
        return (
                self.request.user.is_authenticated
                and self.request.user.has_access_to_product(soccer)
        )


class AiAssistantView(TemplateView):
    template_name = "core/pages/ai_assistant.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("AI Analyst")
        context["hide_footer"] = True
        context["hide_ai_button"] = True
        context["has_access"] = (
                self.request.user.is_authenticated
                and self.request.user.has_access_to_product(
            Product.objects.get(name=Product.Names.AI_ANALYST)
        )
        )
        return context


class SubscriptionRequiredView(TemplateView):
    template_name = "core/pages/subscription_required.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Subscription Required")
        return context
