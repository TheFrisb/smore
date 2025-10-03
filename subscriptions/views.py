from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from core.utils import is_request_from_switzerland
from .models import *


# Create your views here.
class PlansView(TemplateView):
    template_name = "subscriptions/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_subscriptions = self._get_user_subscriptions()

        context["page_title"] = _("Plans")
        context["available_products"] = self._get_products_with_benefits()
        context["available_product_ids"] = [
            product.id for product in context["available_products"]
        ]
        context["user_subscriptions"] = user_subscriptions
        context["owned_price_ids"] = self._get_owned_price_ids(user_subscriptions)
        context["button_text"] = self._get_button_text()
        return context

    def _get_user_subscriptions(self):
        return UserSubscription.objects.filter(
            user=self.request.user, is_active=True
        ).select_related(
            "product_price",
            "product_price__product",
        )

    def _get_owned_price_ids(
        self, user_subscriptions: QuerySet[UserSubscription, UserSubscription]
    ):
        price_ids = []

        for subscription in user_subscriptions:
            price_ids.append(subscription.product_price.id)

        return price_ids

    def _get_button_text(self):
        if self.request.user.is_anonymous:
            return _("Get Started")
        elif self.request.user.subscription_is_active:
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
        prices_query = ProductPrice.objects.filter(currency=currency).order_by("amount")

        return (
            Product.objects.all()
            .order_by("order")
            .prefetch_related(models.Prefetch("prices", queryset=prices_query))
        )
