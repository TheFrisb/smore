from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from core.models import Prediction
from .serializers import PredictionSerializer


class PredictionPagination(PageNumberPagination):
    page_size = 20  # Number of predictions per page
    page_size_query_param = "page_size"


class PaginatedPredictionView(ListAPIView):
    authentication_classes = []
    queryset = Prediction.objects.filter(
        visibility=Prediction.Visibility.PUBLIC,
        status__in=[Prediction.Status.WON, Prediction.Status.LOST],
    ).order_by("-kickoff_date", "-kickoff_time")
    serializer_class = PredictionSerializer
    pagination_class = PredictionPagination
