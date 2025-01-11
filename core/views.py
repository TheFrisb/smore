from django.views.generic import TemplateView


# Create your views here.
class HomeView(TemplateView):
    template_name = "core/pages/home.html"


class HistoryView(TemplateView):
    template_name = "core/pages/history.html"


class PlansView(TemplateView):
    template_name = "core/pages/plans.html"


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
