import logging

from django.views.generic import TemplateView

from core.models import Product, Addon

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/pages/home.html"

    def dispatch(self, request, *args, **kwargs):
        referral_code = request.GET.get("ref", None)
        if referral_code:
            logger.info(f"Home page visited with referral code: {referral_code}")
            request.session["referral_code"] = referral_code

        return super().dispatch(request, *args, **kwargs)


class HistoryView(TemplateView):
    template_name = "core/pages/history.html"


class PlansView(TemplateView):
    template_name = "core/pages/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()
        context["addons"] = Addon.objects.all().order_by("order")

        return context


class FaqView(TemplateView):
    template_name = "core/pages/faq.html"


class HowToJoinView(TemplateView):
    template_name = "core/pages/how_to_join.html"


class AboutUsView(TemplateView):
    template_name = "core/pages/about_us.html"


class ContactUsView(TemplateView):
    template_name = "core/pages/contact_us.html"


class TermsOfServiceView(TemplateView):
    template_name = "core/pages/terms_of_service.html"


class PrivacyPolicyView(TemplateView):
    template_name = "core/pages/privacy_policy.html"


class DisclaimerView(TemplateView):
    template_name = "core/pages/disclaimer.html"


class CookiesPolicyView(TemplateView):
    template_name = "core/pages/cookies_policy.html"


class UpcomingMatchesView(TemplateView):
    template_name = "core/pages/home.html"
