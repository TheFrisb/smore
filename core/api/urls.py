from django.urls import path

from core.api.views import (
    GetFrequentlyAskedQuestionsListView,
    HistoryAPIView,
    ProductsListView,
    UpcomingAPIView,
)

app_name = "core_api"
urlpatterns = [
    path("products/", ProductsListView.as_view(), name="products-list"),
    path(
        "frequently-asked-questions/",
        GetFrequentlyAskedQuestionsListView.as_view(),
        name="faq-api",
    ),
    path(
        "history/paginated-predictions/",
        HistoryAPIView.as_view(),
        name="paginated-predictions-history",
    ),
    path(
        "upcoming/",
        UpcomingAPIView.as_view(),
        name="upcoming-predictions-tickets",
    ),
]
