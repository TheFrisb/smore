from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from accounts.serializers import ProductSerializer
from core.models import Prediction, Product, FrequentlyAskedQuestion, Ticket
from .serializers import (
    PredictionSerializer,
    FrequentlyAskedQuestionSerializer,
    PredictionHistorySerializer,
    TicketHistorySerializer,
)


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
    permission_classes = []

    def get_queryset(self):
        return (
            Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
                status=Prediction.Status.PENDING,
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


class GetFrequentlyAskedQuestionsListView(ListAPIView):
    serializer_class = FrequentlyAskedQuestionSerializer
    permission_classes = []

    def get_queryset(self):
        return FrequentlyAskedQuestion.objects.all().order_by("order")


class HistoryAPIView(APIView):
    pagination_class = PredictionPagination
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        # Existing queryset logic remains unchanged
        product_filter = self.request.query_params.get("filter")
        obj_filter = self.request.query_params.get("obj")

        predictions = []
        tickets = []

        if obj_filter is None or obj_filter == "predictions":
            predictions = Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
                status__in=[Prediction.Status.WON, Prediction.Status.LOST],
            ).select_related(
                "match__home_team", "match__away_team", "match__league", "product"
            )
            if product_filter:
                predictions = predictions.filter(product__name=product_filter)

        if obj_filter is None or obj_filter == "tickets":
            tickets = Ticket.objects.filter(
                visibility=Ticket.Visibility.PUBLIC,
                status__in=[Ticket.Status.WON, Ticket.Status.LOST],
            ).prefetch_related(
                "bet_lines__match__home_team",
                "bet_lines__match__away_team",
                "bet_lines__match__league",
                "product",
            )
            if product_filter:
                tickets = tickets.filter(product__name=product_filter)

        return predictions, tickets

    def get(self, request):
        predictions, tickets = self.get_queryset()

        # Serialize data
        prediction_data = PredictionHistorySerializer(predictions, many=True).data
        ticket_data = TicketHistorySerializer(tickets, many=True).data

        # Combine and sort
        combined = []
        for p in prediction_data:
            p["datetime"] = p["match"]["kickoff_datetime"]
            combined.append(p)

        for t in ticket_data:
            t["datetime"] = t["starts_at"]
            combined.append(t)

        # Sort descending by datetime
        combined.sort(key=lambda x: x["datetime"], reverse=True)

        # Paginate results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


class UpcomingAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        product_filter = self.request.query_params.get("filter")
        obj_filter = self.request.query_params.get("obj")

        predictions = []
        tickets = []

        if obj_filter is None or obj_filter == "predictions":
            predictions = Prediction.objects.filter(
                visibility=Prediction.Visibility.PUBLIC,
                status=Prediction.Status.PENDING,
            ).select_related(
                "match__home_team", "match__away_team", "match__league", "product"
            ).exclude(id=1024).order_by("match__kickoff_datetime")
            
            if product_filter:
                predictions = predictions.filter(product__name=product_filter)

        if obj_filter is None or obj_filter == "tickets":
            tickets = Ticket.objects.filter(
                visibility=Ticket.Visibility.PUBLIC,
                status=Ticket.Status.PENDING,
                starts_at__date__gte=timezone.now().date(),
            ).prefetch_related(
                "bet_lines__match__home_team",
                "bet_lines__match__away_team",
                "bet_lines__match__league",
                "product",
            ).order_by("product__name", "starts_at")
            
            if product_filter:
                tickets = tickets.filter(product__name=product_filter)

        return predictions, tickets

    def get(self, request):
        predictions, tickets = self.get_queryset()

        # Serialize data
        prediction_data = PredictionSerializer(predictions, many=True).data
        ticket_data = TicketHistorySerializer(tickets, many=True).data

        # Combine and add metadata for sorting
        combined = []
        for p in prediction_data:
            p["type"] = "prediction"
            p["datetime"] = p["match"]["kickoff_datetime"]
            combined.append(p)

        for t in ticket_data:
            t["type"] = "ticket"
            t["datetime"] = t["starts_at"]
            combined.append(t)

        # Sort by type (ticket comes first) and then by datetime
        # This matches the UpcomingMatchesView sorting logic
        combined.sort(key=lambda x: (x["type"] != "ticket", x["datetime"]))

        return Response(combined)
