from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User


class UserService:
    def __init__(self, mail_service):
        self.mail_service = mail_service
        self.token_generator = PasswordResetTokenGenerator()

    def send_password_change_link(self, user: User, request: Request):
        """
        Initiates a password reset process for the given email.
        Returns True if successful, False if user not found.
        """

        token = self.token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the password reset URL
        reset_url = self.request.build_absolute_uri(
            reverse_lazy(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            )
        )

        # Log and send the email
        logger.info(f"Password reset link for {user.username}: {reset_url}")
        self.mail_service.send_reset_password_email(user, reset_url)

        return True
