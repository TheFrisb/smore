from django.urls import path

from .views import HomeView, HistoryView, PlansView, FaqView, HowToJoinView

app_name = "core"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("history/", HistoryView.as_view(), name="history"),
    path("plans/", PlansView.as_view(), name="plans"),
    path("frequently-asked-questions/", FaqView.as_view(), name="faq"),
    path("how-to-join/", HowToJoinView.as_view(), name="how_to_join"),
]
