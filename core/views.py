import logging
from collections import defaultdict
from itertools import groupby

from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from accounts.models import (
    PurchasedDailyOffer,
    PurchasedPredictions,
    PurchasedTickets,
    User,
)
from ai_assistant.models import Message, SuggestedMessage
from core.models import (
    FrequentlyAskedQuestion,
    PickOfTheDay,
    Prediction,
    Ticket,
)
from subscriptions.models import Product

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
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get combined and sorted objects
        combined_objects = self._get_combined_objects()

        # Paginate results
        paginator = Paginator(combined_objects, self.paginate_by)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "filter_product": Product.objects.filter(
                    name=self._get_product_filter()
                ).first(),
                "filter_object": self._get_object_filter(),
                "pick_of_the_day": PickOfTheDay.get_solo(),
                "page_title": _("Historical Results"),  # Updated title
                "allowed_products": self.get_allowed_products(),
                "purchased_ids": self.get_purchased_ids(),
                "products": Product.objects.filter(
                    name__in=[
                        Product.Names.SOCCER,
                        Product.Names.BASKETBALL,
                        Product.Names.NFL_NHL,
                        Product.Names.TENNIS,
                    ]
                ).order_by("order"),
                "base_url": "core:history",
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
            }
        )
        return context

    def _get_combined_objects(self):
        """Combine and sort predictions/tickets like the API"""
        predictions, tickets = self._get_filtered_querysets()

        # Create unified object list
        combined = []
        for pred in predictions:
            combined.append(
                {
                    "object": pred,
                    "type": "prediction",
                    "datetime": pred.match.kickoff_datetime,
                }
            )

        for ticket in tickets:
            bet_lines = list(ticket.bet_lines.all())
            for i, bet_line in enumerate(bet_lines):
                # Add grouping flags to bet line instance
                bet_line.same_as_previous = False
                bet_line.same_as_next = False

                if i > 0 and bet_lines[i - 1].match == bet_line.match:
                    bet_line.same_as_previous = True

                if i < len(bet_lines) - 1 and bet_lines[i + 1].match == bet_line.match:
                    bet_line.same_as_next = True
            combined.append(
                {"object": ticket, "type": "ticket", "datetime": ticket.starts_at}
            )

        # Sort descending like the API
        return sorted(combined, key=lambda x: x["datetime"], reverse=True)

    def _get_filtered_querysets(self):
        """Replicate API's filtering logic"""
        product_filter = self._get_product_filter()
        obj_filter = self._get_object_filter()

        predictions = Prediction.objects.none()
        tickets = Ticket.objects.none()

        if obj_filter in [None, "predictions"]:
            predictions = Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
                status__in=[Prediction.Status.WON, Prediction.Status.LOST],
            ).select_related(
                "match__home_team", "match__away_team", "match__league", "product"
            )
            if product_filter:
                predictions = predictions.filter(product__name=product_filter)

        if obj_filter in [None, "tickets"]:
            tickets = Ticket.objects.filter(
                visibility=Ticket.Visibility.PUBLIC,
                status__in=[Ticket.Status.WON, Ticket.Status.LOST],
            ).prefetch_related(
                "bet_lines__match__home_team",
                "bet_lines__match__away_team",
                "bet_lines__match__league",
            )
            if product_filter:
                tickets = tickets.filter(product__name=product_filter)

        return predictions, tickets

    def _get_product_filter(self):
        """
        Get the filter from the request.
        """
        return self.request.GET.get("filter", None)

    def _get_object_filter(self):
        """
        Get the filter for the object.
        """
        return self.request.GET.get("obj", None)

    def _get_predictions(self, filter):
        """
        Get the predictions based on the filter.
        """
        predictions = (
            Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
                status__in=[
                    Prediction.Status.WON,
                    Prediction.Status.LOST,
                ],
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

        return predictions

    def _get_tickets(self, filter):
        """
        Get the tickets based on the filter.
        """
        sport_tickets = (
            Ticket.objects.filter(
                visibility=Ticket.Visibility.PUBLIC,
                status__in=[Ticket.Status.WON, Ticket.Status.LOST],
            )
            .prefetch_related(
                "bet_lines",
                "bet_lines__match",
                "bet_lines__match__home_team",
                "bet_lines__match__away_team",
                "bet_lines__match__league",
            )
            .order_by("starts_at")
        )

        if filter:
            sport_tickets = sport_tickets.filter(product__name=filter)

        """
            Loop over all tickets and their bet lines.
            If a bet line has the same match as the next bet line, add has_same_next=True,
            If a bet line has the same match as the previous bet line, add has_same_previous=True.
        """

        for ticket in sport_tickets:
            for i, bet_line in enumerate(ticket.bet_lines.all()):
                if i < len(ticket.bet_lines.all()) - 1:
                    next_bet_line = ticket.bet_lines.all()[i + 1]
                    if bet_line.match == next_bet_line.match:
                        bet_line.has_same_next = True
                    else:
                        bet_line.has_same_next = False

                if i > 0:
                    previous_bet_line = ticket.bet_lines.all()[i - 1]
                    if bet_line.match == previous_bet_line.match:
                        bet_line.has_same_previous = True
                    else:
                        bet_line.has_same_previous = False

        return sport_tickets

    def get_purchased_ids(self):
        """
        Get IDs of purchased predictions for the current user.
        """
        if not self.request.user.is_authenticated:
            return []

        sport_tickets = PurchasedTickets.objects.filter(
            user=self.request.user
        ).values_list("ticket_id", flat=True)

        purchased_predictions = PurchasedPredictions.objects.filter(
            user=self.request.user
        ).values_list("prediction_id", flat=True)

        return list(sport_tickets) + list(purchased_predictions)

    def get_allowed_products(self):
        """
        Get product IDs the user has access to.
        """

        return Product.objects.all().values_list("id", flat=True)


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

        if PurchasedDailyOffer.objects.filter(
            user=self.request.user if self.request.user.is_authenticated else None,
            status=PurchasedDailyOffer.Status.PURCHASED,
            for_date=timezone.now().date(),
        ).exists():
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


class TelegramLandingView(TemplateView):
    template_name = "core/pages/telegram_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Free Telegram Channel")
        return context


class ReferralTelegramLandingView(TemplateView):
    template_name = "core/pages/telegram_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Free Telegram Channel")
        context["referred_user"] = self._get_user()
        return context

    def _get_user(self):
        return User.objects.filter(id=312).first()


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

        # Add existing context variables from the original view
        context["filter_product"] = Product.objects.filter(
            name=self._get_product_filter()
        ).first()
        context["filter_object"] = self._get_object_filter()
        context["pick_of_the_day"] = PickOfTheDay.get_solo()
        context["page_title"] = _("Upcoming Matches")
        context["allowed_products"] = self.get_allowed_products()
        context["purchased_ids"] = self.get_purchased_ids()
        context["products"] = Product.objects.filter(
            name__in=[
                Product.Names.SOCCER,
                Product.Names.BASKETBALL,
                Product.Names.NFL_NHL,
                Product.Names.TENNIS,
            ]
        ).order_by("order")
        context["base_url"] = "core:upcoming_matches"

        context["grouped_items"] = self._get_grouped_objects()
        context["has_daily_offer"] = PurchasedDailyOffer.objects.filter(
            user=self.request.user if self.request.user.is_authenticated else None,
            status=PurchasedDailyOffer.Status.PURCHASED,
            for_date=timezone.now().date(),
        ).exists()

        can_not_view_at_least_one = any(
            item["object"].product.id not in context["allowed_products"]
            and item["object"].id not in context["purchased_ids"]
            for date, items in context["grouped_items"]
            for item in items
        )
        context["can_not_view_at_least_one_prediction"] = can_not_view_at_least_one

        return context

    def _get_product_filter(self):
        """
        Get the filter from the request.
        """
        return self.request.GET.get("filter", None)

    def _get_object_filter(self):
        """
        Get the filter for the object.
        """
        return self.request.GET.get("obj", None)

    def _get_visibility_filter(self):
        visibility = [Prediction.Visibility.PUBLIC]
        if self.request.user.is_superuser:
            visibility.append(Prediction.Visibility.ADMIN)

        return visibility

    def _get_predictions(self, filter):
        """
        Get the predictions based on the filter.
        """
        predictions = (
            Prediction.objects.filter(
                visibility__in=self._get_visibility_filter(),
                status=Prediction.Status.PENDING,
            )
            .select_related(
                "match",
                "match__home_team",
                "match__away_team",
                "match__league",
                "product",
            )
            .exclude(id=1053)
            .order_by("match__kickoff_datetime")
        )

        if filter:
            predictions = predictions.filter(product__name=filter)

        return predictions

    def _get_tickets(self, filter):
        """
        Get the tickets based on the filter.
        """
        sport_tickets = (
            Ticket.objects.filter(
                visibility__in=self._get_visibility_filter(),
                status=Ticket.Status.PENDING,
                starts_at__date__gte=timezone.now().date(),
            )
            .prefetch_related(
                "bet_lines",
                "bet_lines__match",
                "bet_lines__match__home_team",
                "bet_lines__match__away_team",
                "bet_lines__match__league",
            )
            .order_by("product__name", "starts_at")
        )

        if filter:
            sport_tickets = sport_tickets.filter(product__name=filter)

        for ticket in sport_tickets:
            for i, bet_line in enumerate(ticket.bet_lines.all()):
                if i < len(ticket.bet_lines.all()) - 1:
                    next_bet_line = ticket.bet_lines.all()[i + 1]
                    if bet_line.match == next_bet_line.match:
                        bet_line.has_same_next = True
                    else:
                        bet_line.has_same_next = False

                if i > 0:
                    previous_bet_line = ticket.bet_lines.all()[i - 1]
                    if bet_line.match == previous_bet_line.match:
                        bet_line.has_same_previous = True
                    else:
                        bet_line.has_same_previous = False

        return sport_tickets

    def _get_grouped_objects(self):
        """
        Group predictions and sport tickets by date and sort by datetime within each date.
        """
        predictions, sport_tickets = None, None

        product_filter = self._get_product_filter()
        obj_filter = self._get_object_filter()

        if obj_filter is None or obj_filter == "predictions":
            predictions = self._get_predictions(product_filter)

        if obj_filter is None or obj_filter == "tickets":
            sport_tickets = self._get_tickets(product_filter)

        # Combine objects with type and datetime information
        all_objects = []
        if predictions:
            for pred in predictions:
                all_objects.append(
                    {
                        "object": pred,
                        "type": "prediction",
                        "datetime": pred.match.kickoff_datetime,
                    }
                )

        if sport_tickets:
            for ticket in sport_tickets:
                # Process bet lines for match grouping
                bet_lines = list(ticket.bet_lines.all())
                for i, bet_line in enumerate(bet_lines):
                    # Add grouping flags to bet line instance
                    bet_line.same_as_previous = False
                    bet_line.same_as_next = False

                    if i > 0 and bet_lines[i - 1].match == bet_line.match:
                        bet_line.same_as_previous = True

                    if (
                        i < len(bet_lines) - 1
                        and bet_lines[i + 1].match == bet_line.match
                    ):
                        bet_line.same_as_next = True

                all_objects.append(
                    {"object": ticket, "type": "ticket", "datetime": ticket.starts_at}
                )

        # Group by date
        grouped_by_date = defaultdict(list)
        for item in all_objects:
            date = item["datetime"].date()
            grouped_by_date[date].append(item)

        # Sort each group by datetime
        for date, items in grouped_by_date.items():
            # Sort by type (ticket comes first) and then by datetime
            grouped_by_date[date] = sorted(
                items, key=lambda x: (x["type"] != "ticket", x["datetime"])
            )

        # Create a sorted list of (date, items) for the template
        sorted_dates = sorted(grouped_by_date.keys())
        grouped_items = [(date, grouped_by_date[date]) for date in sorted_dates]

        return grouped_items

    def get_purchased_ids(self):
        """
        Get IDs of purchased predictions for the current user.
        """
        if not self.request.user.is_authenticated:
            return []

        sport_tickets = PurchasedTickets.objects.filter(
            user=self.request.user
        ).values_list("ticket_id", flat=True)

        purchased_predictions = PurchasedPredictions.objects.filter(
            user=self.request.user
        ).values_list("prediction_id", flat=True)

        return list(sport_tickets) + list(purchased_predictions)

    def get_allowed_products(self):
        """
        Get product IDs the user has access to.
        """
        user = self.request.user

        if not user.is_authenticated:
            return []

        return (
            Product.objects.filter(
                prices__user_subscriptions__user=user,
                prices__user_subscriptions__is_active=True,
            )
            .distinct()
            .values_list("id", flat=True)
        )


class AiAssistantView(TemplateView):
    template_name = "core/pages/ai_assistant.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("AI Analyst")
        context["hide_footer"] = True
        context["hide_ai_button"] = True
        context["free_messages"] = self.get_free_messages()
        context["ai_assistant_product_id"] = Product.objects.get(
            name=Product.Names.AI_ANALYST
        ).id
        context["has_access"] = self._can_text_ai_assistant()
        context["suggested_messages"] = self._get_suggested_messages()
        return context

    def _can_text_ai_assistant(self):
        """
        Check if the user can text the AI Assistant.
        """
        user = self.request.user

        if not user.is_authenticated:
            return False

        if self._get_has_access():
            return True

        # Check if the user has free messages left
        free_messages = self.get_free_messages()
        if free_messages is not None and free_messages > 0:
            return True

        return False

    def _get_suggested_messages(self):
        return SuggestedMessage.objects.all().order_by("order")

    def _get_has_access(self):
        """
        Check if the user has access to the AI Assistant product.
        """
        user = self.request.user

        if user.is_authenticated:
            return user.has_access_to_product(Product.Names.AI_ANALYST)
        return False

    def get_free_messages(self):
        user = self.request.user

        if not user.is_authenticated:
            return None

        if self._get_has_access():
            return None

        msg_count = Message.objects.filter(
            user=user, direction=Message.Direction.OUTBOUND
        ).count()

        if msg_count < 3:
            return 3 - msg_count
        else:
            return 0


class SubscriptionRequiredView(TemplateView):
    template_name = "core/pages/subscription_required.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Subscription Required")
        return context


class VerifyEmailView(TemplateView):
    template_name = "core/pages/verify-email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Verify your email")
        return context
