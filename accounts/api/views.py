from django.contrib import messages
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.serializers import WithdrawalRequestSerializer
from core.mailer.mailjet_service import MailjetService


class CreateWithdrawalRequestView(APIView):
    def __init__(self):
        super().__init__()
        self.mail_service = MailjetService()

    def post(self, request):
        serializer = WithdrawalRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        messages.success(
            request,
            "Your withdrawal request has been submitted successfully. You'll receive an email once it's processed.",
        )

        withdrawal_request = serializer.save()
        self.mail_service.send_withdrawal_request_email(withdrawal_request)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
