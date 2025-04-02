from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.serializers import ProductSerializer
from core.models import Prediction, Product
from .serializers import PredictionSerializer


class PredictionPagination(PageNumberPagination):
    page_size = 20  # Number of predictions per page
    page_size_query_param = "page_size"
    page_query_param = "page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,  # Total number of predictions
                "total_pages": self.page.paginator.num_pages,  # Total pages
                "current_page": self.page.number,  # Current page number
                "page_size": self.page.paginator.per_page,  # Items per page
                "next": self.get_next_link(),  # URL to next page
                "previous": self.get_previous_link(),  # URL to previous page
                "results": data,  # Actual paginated data
            }
        )


class PredictionFilter(filters.FilterSet):
    product = filters.CharFilter(field_name="product__name")
    date = filters.DateFilter(field_name="match__kickoff_datetime", lookup_expr="date")

    class Meta:
        model = Prediction
        fields = ["product"]


class ProductsListView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all().order_by("order")


class PaginatedHistoryPredictionsView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    filterset_class = PredictionFilter
    queryset = (
        Prediction.objects.filter(
            visibility=Prediction.Visibility.PUBLIC,
            status__in=[Prediction.Status.WON, Prediction.Status.LOST],
        )
        .prefetch_related(
            "match",
            "match__league",
            "match__home_team",
            "match__away_team",
            "match__league__country",
        )
        .order_by("-match__kickoff_datetime")
    )
    serializer_class = PredictionSerializer
    pagination_class = PredictionPagination


class PredictionListView(ListAPIView):
    serializer_class = PredictionSerializer
    filterset_class = PredictionFilter

    def get_queryset(self):
        return (
            Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
            )
            .prefetch_related(
                "match",
                "match__league",
                "match__home_team",
                "match__away_team",
                "match__league__country",
            )
            .order_by("match__kickoff_datetime")
        )
