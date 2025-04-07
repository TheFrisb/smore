import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User
from core.mailer.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.mail_service = MailjetService()
        self.token_generator = PasswordResetTokenGenerator()

    def send_password_change_link(self, user: User):
        """
        Initiates a password reset process for the given email.
        Returns True if successful, False if user not found.
        """

        token = self.token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the password reset URL
        view_url = reverse_lazy(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )
        reset_url = f"{settings.BASE_URL}{view_url}"

        # Log and send the email
        logger.info(f"Password reset link for {user.username}: {reset_url}")
        self.mail_service.send_reset_password_email(user, reset_url)
