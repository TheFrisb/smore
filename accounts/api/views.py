import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserBalance
from accounts.serializers import WithdrawalRequestSerializer
from core.mailer.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


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

        user_balance = UserBalance.objects.filter(user=request.user).first()
        user_balance.balance -= serializer.validated_data["amount"]
        user_balance.save()

        withdrawal_request = serializer.save()
        self.mail_service.send_withdrawal_request_email(withdrawal_request)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostSendConfirmEmailMailView(APIView):
    def __init__(self):
        super().__init__()
        self.mail_service = MailjetService()

    def post(self, request):
        user = request.user

        if not user.is_email_verified:
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            confirmation_link = settings.BASE_URL + reverse(
                "accounts:verify_email", kwargs={"uidb64": uidb64, "token": token}
            )

            logger.info(f"Sending email confirmation link to {user.email}")

            self.mail_service.send_email_confirmation_email(user, confirmation_link)

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteMyAccountView(APIView):
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        
        messages.success(request, "Your account has been deleted successfully.")
        return Response(status=status.HTTP_204_NO_CONTENT)
