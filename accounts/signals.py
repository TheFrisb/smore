import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User, UserBalance
from core.mailer.mailjet_service import MailjetService
from payments.services.stripe.base_stripe_service import BaseStripeService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_balance(sender, instance: User, created, **kwargs):
    if created:
        UserBalance.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_user_referral_code(sender, instance: User, created, **kwargs):
    if created:
        instance.referral_code = instance.generate_referral_code()
        instance.save()


@receiver(post_save, sender=User)
def create_stripe_customer(sender, instance: User, created, **kwargs):
    if created:
        service = BaseStripeService()
        service.create_stripe_customer(instance)


@receiver(post_save, sender=User)
def send_email_confirmation_token(sender, instance: User, created, **kwargs):
    """
    Generates a token and sends an email confirmation link.
    This runs ONLY when a new User row is created.
    """
    if created and not instance.is_email_verified:
        # If you're *not* defaulting to is_active=False in the model,
        # and want to disable them here, you can do:
        # instance.is_active = False
        # instance.save(update_fields=["is_active"])

        # 1. Generate token
        token = default_token_generator.make_token(instance)
        uidb64 = urlsafe_base64_encode(force_bytes(instance.pk))

        # 2. Build confirmation link
        # e.g. "https://yoursite.com/accounts/verify-email/<uidb64>/<token>/"
        confirmation_link = settings.BASE_URL + reverse(
            "accounts:verify_email", kwargs={"uidb64": uidb64, "token": token}
        )

        # 3. Send the email
        mail_service = MailjetService()
        mail_service.send_email_confirmation_email(
            user=instance, confirmation_link=confirmation_link
        )
        logger.info(f"Email confirmation link sent to {instance.email}")
