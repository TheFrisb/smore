from django.contrib import messages
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.serializers import WithdrawalRequestSerializer


class CreateWithdrawalRequestView(APIView):
    def post(self, request):
        serializer = WithdrawalRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        messages.success(
            request,
            "Your withdrawal request has been submitted successfully. You'll receive an email once it's processed.",
        )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
