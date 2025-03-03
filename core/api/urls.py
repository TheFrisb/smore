from django.urls import path

from core.api.views import PaginatedPredictionView, PredictionListView

urlpatterns = [
    path("history/predictions/", PaginatedPredictionView.as_view(), name="predictions-api"),

    path('predictions/', PredictionListView.as_view(), name='predictions-list'),
]
