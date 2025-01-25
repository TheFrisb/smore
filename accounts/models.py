import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import BaseInternalModel

logger = logging.getLogger(__name__)


# Create your models here.
class User(BaseInternalModel, AbstractUser):
    """
    Custom User model to store user details.
    """

    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def referral_link(self):
        """
        Generate a referral link for the user
        """
        return f"{settings.BASE_URL}/?ref={self.referral_code}"

    @property
    def subscription_is_active(self):
        """
        Check if the user has an active subscription.
        """
        user_subscription = getattr(self, "subscription", None)
        if not user_subscription:
            return False

        return user_subscription.is_active

    @property
    def available_balance(self):
        """
        Get the available balance for the user.
        """
        user_balance = getattr(self, "balance", None)
        if not user_balance:
            return 0

        return user_balance.balance

    def generate_referral_code(self):
        """
        Generate a random referral code for the user
        """
        length = 12
        characters = string.ascii_letters + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))


class UserBalance(BaseInternalModel):
    """
    UserBalance model to track the balance of each user.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="balance")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"


class Referral(BaseInternalModel):
    class Level(models.IntegerChoices):
        DIRECT = 1, "Direct"
        INDIRECT = 2, "Indirect"

    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals"
    )
    referred = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referred_by"
    )
    level = models.PositiveSmallIntegerField(choices=Level)

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred.username}"

    @staticmethod
    def get_second_level_referrals(user: User):
        """
        Fetch second-level referrals for the given user.
        """
        first_level = Referral.objects.filter(referrer=user).values_list(
            "referred", flat=True
        )
        second_level = Referral.objects.filter(referrer__in=first_level).select_related(
            "referrer", "referred"
        )
        return second_level

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(referrer=models.F("referred")),
                name="referrer_not_referred",
            ),
        ]


class WithdrawalRequest(BaseInternalModel):
    class Status(models.IntegerChoices):
        PENDING = 1, "Pending"
        APPROVED = 2, "Approved"
        PROCESSING = 3, "Processing"
        COMPLETED = 4, "Completed"
        REJECTED = 5, "Rejected"

    class PayoutType(models.TextChoices):
        BANK = "BANK", "Bank"
        PAYONEER = "PAYONEER", "Payoneer"
        CRYPTOCURRENCY = "CRYPTOCURRENCY", "Cryptocurrency"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.PENDING)
    payout_type = models.CharField(max_length=20, choices=PayoutType)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    iban = models.CharField(max_length=255, blank=True, null=True)
    cryptocurrency_address = models.CharField(max_length=255, blank=True, null=True)
    payoneer_customer_id = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


class UserSubscription(BaseInternalModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class Frequency(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription"
    )
    status = models.CharField(max_length=10, choices=Status, default=Status.INACTIVE)
    frequency = models.CharField(max_length=10, choices=Frequency)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    products = models.ManyToManyField("core.Product", related_name="subscriptions")

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_monthly(self):
        return self.frequency == self.Frequency.MONTHLY

    @property
    def next_billing_date(self):
        return self.end_date

    def __str__(self):
        return f"{self.get_status_display()} {self.get_frequency_display()} subscription for {self.user.username}"


class ReferralEarning(BaseInternalModel):
    """
    Tracks each commission earned (e.g., 20% direct, 5% indirect, etc.)
    """

    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="earnings"
    )
    # The user who *receives* the commission
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referral_earnings"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.receiver.username} - {self.amount}"
