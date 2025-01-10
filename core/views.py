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
