from datetime import datetime

from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from core.utils import is_request_from_switzerland

from .models import *


# Create your views here.
class PlansView(TemplateView):
    template_name = "subscriptions/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_user_subscriptions = self._get_user_subscriptions()

        context["page_title"] = _("Plans")
        context["available_products"] = self._get_products_with_benefits()
        context["available_product_ids"] = [
            product.id for product in context["available_products"]
        ]
        context["user_subscriptions"] = active_user_subscriptions
        context["first_active_product"] = self._get_first_active_product(
            active_user_subscriptions
        )
        context["owned_discounted_product"] = self._get_owned_discounted_products(
            active_user_subscriptions
        )
        context["owned_price_ids"] = self._get_owned_price_ids(
            active_user_subscriptions
        )
        context["owned_product_ids"] = self._get_owned_product_ids(
            active_user_subscriptions
        )
        context["purchased_product_ids"] = self.get_purchased_product_ids()
        context["button_text"] = self._get_button_text()
        return context

    def _get_user_subscriptions(self):
        if not self.request.user.is_authenticated:
            return UserSubscription.objects.none()

        return UserSubscription.objects.filter(
            user=self.request.user, is_active=True
        ).select_related(
            "product_price",
            "product_price__product",
        )

    def _get_first_active_product(
        self, user_subscriptions: QuerySet[UserSubscription, UserSubscription]
    ):
        if not self.request.user.is_authenticated or not user_subscriptions:
            return None

        return sorted(user_subscriptions, key=lambda instance: instance.created_at)[
            0
        ].product_price.product

    def _get_owned_discounted_products(
        self, user_subscriptions: QuerySet[UserSubscription, UserSubscription]
    ):
        products = []

        for subscription in user_subscriptions:
            if subscription.is_discounted:
                products.append(subscription.product_price.product)

        return products

    def _get_owned_price_ids(
        self, user_subscriptions: QuerySet[UserSubscription, UserSubscription]
    ):
        price_ids = []

        for subscription in user_subscriptions:
            price_ids.append(subscription.product_price.id)

        return price_ids

    def _get_owned_product_ids(
        self, user_subscriptions: QuerySet[UserSubscription, UserSubscription]
    ):
        product_ids = []

        for subscription in user_subscriptions:
            product_ids.append(subscription.product_price.product.id)

        return product_ids

    def _get_button_text(self):
        if self.request.user.is_anonymous:
            return _("Get Started")
        elif self.request.user.has_active_subscription:
            return _("Update Plan")
        else:
            return _("Subscribe Now")

    def _get_products_with_benefits(self):
        products = self._get_products_with_ordered_prices()

        for product in products:
            product.benefits = self._construct_benefit_list(product)

        return products

    def _construct_benefit_list(self, product: Product):
        benefits = []

        if product.name == Product.Names.AI_ANALYST:
            benefits.append(_("AI Bet Builder"))
            benefits.append(_("Deep Match Analysis"))
            benefits.append(_("Real-Time News"))
            benefits.append(_("Tailored Ticket Generator"))

            return benefits

        analysis_per_month_label = _("analyses per month")

        benefits.append(f"{product.analysis_per_month} {analysis_per_month_label}")
        benefits.append(_("Daily Ticket Suggestions"))
        benefits.append(_("High Odds"))
        benefits.append(_("Betting Guidance"))
        benefits.append(_("Promotions & Giveaways"))
        benefits.append(_("24/7 Client Support"))
        benefits.append(_("Affiliate Program"))

        return benefits

    def _get_products_with_ordered_prices(self):
        currency = "CHF" if is_request_from_switzerland(self.request) else "€"
        prices_query = ProductPrice.objects.filter(
            currency=currency, provider=BillingProvider.STRIPE
        ).order_by("amount")

        v1_threshold_datetime = timezone.make_aware(datetime(2025, 9, 1))

        if (
            not self.request.user.is_authenticated
            or not UserSubscription.objects.filter(
                user=self.request.user, start_date__lt=v1_threshold_datetime
            ).exists()
        ):
            prices_query = prices_query.filter(version=2)
        else:
            subquery = ProductPrice.objects.filter(
                version=1,
                product_id=OuterRef("product_id"),
                currency=OuterRef("currency"),
                provider=OuterRef("provider"),
                interval=OuterRef("interval"),
                interval_count=OuterRef("interval_count"),
            )
            prices_query = prices_query.filter(
                Q(version=1) | (Q(version=2) & ~Exists(subquery))
            )

        return (
            Product.objects.all()
            .order_by("order")
            .prefetch_related(models.Prefetch("prices", queryset=prices_query))
        )

    def get_purchased_product_ids(self):
        owned_product_ids = []

        if not self.request.user.is_authenticated:
            return owned_product_ids

        user_subscriptions = UserSubscription.objects.filter(
            user=self.request.user, provider=BillingProvider.STRIPE
        ).prefetch_related("product_price", "product_price__product")

        if not user_subscriptions:
            return owned_product_ids

        for subscription in user_subscriptions:
            product = subscription.product_price.product
            if product.id not in owned_product_ids:
                owned_product_ids.append(product.id)

        return owned_product_ids
