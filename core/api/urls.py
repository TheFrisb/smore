from django.urls import path

from core.api.views import PaginatedHistoryPredictionsView, PredictionListView, ProductsListView

urlpatterns = [
    path(
        "history/predictions/",
        PaginatedHistoryPredictionsView.as_view(),
        name="predictions-api",
    ),
    path("predictions/", PredictionListView.as_view(), name="predictions-list"),
    path("products/", ProductsListView.as_view(), name="products-list"),
]
