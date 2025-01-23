from django.urls import path

from core.api.views import PaginatedPredictionView

urlpatterns = [
    path("predictions/", PaginatedPredictionView.as_view(), name="predictions-api"),
]
