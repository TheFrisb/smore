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

        return {
            "primary_button_text": _("Upcoming matches"),
            "primary_button_url": reverse("core:upcoming_matches"),
            "primary_button_description": _("View upcoming matches"),
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
        filter = self.request.GET.get("filter", "all")
        if filter == "all":
            context["filter_product"] = None
            context["predictions"] = self.get_history_predictions(None)
        else:
            try:
                product = Product.objects.get(name=filter)
                context["filter_product"] = product
                context["predictions"] = self.get_history_predictions(filter)
            except Product.DoesNotExist:
                context["filter_product"] = None
                context["predictions"] = self.get_history_predictions(None)

        context["page_title"] = _("History")
        context["allowed_prediction_products"] = Product.objects.filter(
            type=Product.Types.SUBSCRIPTION
        ).values_list("id", flat=True)
        context["products"] = Product.objects.filter(
            type=Product.Types.SUBSCRIPTION
        ).order_by("order")
        return context

    def get_history_predictions(self, filter):
        predictions = Prediction.objects.filter(
            visibility=Prediction.Visibility.PUBLIC,
            status__in=[Prediction.Status.WON, Prediction.Status.LOST],
        ).order_by("-match__kickoff_datetime")

        if filter:
            predictions = predictions.filter(product__name=filter)

        return predictions[0:20]


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
        context["user_has_discount"] = self._get_user_has_discount()
        context["page_title"] = _("Plans")

        return context

    def _get_user_has_discount(self):
        if not self.request.user.is_authenticated:
            return False

        return self.request.user.has_sport_discount()


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
        context = super().get_context_data(**kwargs)

        filter = self.request.GET.get("filter", "all")
        if filter == "all":
            print("all")
            context["filter_product"] = None
            context["grouped_predictions"] = self.get_grouped_predictions(None)
        else:
            print(filter)
            try:
                product = Product.objects.get(name=filter)
                print(product.name)
                context["filter_product"] = product
                context["grouped_predictions"] = self.get_grouped_predictions(filter)
            except Product.DoesNotExist:
                context["filter_product"] = None
                context["grouped_predictions"] = self.get_grouped_predictions(None)

        context["pick_of_the_day"] = PickOfTheDay.get_solo()
        context["page_title"] = _("Upcoming Matches")
        context["allowed_prediction_products"] = self.get_allowed_prediction_products()
        context["purchased_prediction_ids"] = self.get_purchased_prediction_ids()
        context["products"] = Product.objects.filter(
            type=Product.Types.SUBSCRIPTION
        ).order_by("order")
        return context

    def get_purchased_prediction_ids(self):
        if not self.request.user.is_authenticated:
            return []

        return PurchasedPredictions.objects.filter(user=self.request.user).values_list(
            "prediction_id", flat=True
        )

    def get_grouped_predictions(self, filter):
        predictions = (
            Prediction.objects.filter(
                match__kickoff_datetime__date__gte=timezone.now().date(),
                visibility=Prediction.Visibility.PUBLIC,
                status=Prediction.Status.PENDING,
            )
            .select_related(
                "match",
                "match__home_team",
                "match__away_team",
                "match__league",
                "product",
            )
            .order_by("match__kickoff_datetime")
        )

        if filter:
            predictions = predictions.filter(product__name=filter)

        grouped_predictions = {
            kickoff_date: list(predictions)
            for kickoff_date, predictions in groupby(
                predictions, key=lambda p: p.match.kickoff_datetime.date()
            )
        }

        return grouped_predictions

    def get_allowed_prediction_products(self):
        allowed_prediction_products = []
        products = Product.objects.filter(type=Product.Types.SUBSCRIPTION)

        if not self.request.user.is_authenticated:
            return allowed_prediction_products

        for product in products:
            if self.request.user.has_access_to_product(product):
                allowed_prediction_products.append(product.id)

        return allowed_prediction_products


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
