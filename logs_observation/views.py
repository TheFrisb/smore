from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from logs_observation.serializers import LogSerializer


class LogCreateView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = LogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
