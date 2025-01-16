import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import BaseInternalModel


# Create your models here.
class User(BaseInternalModel, AbstractUser):
    """
    Custom User model to store user details.
    """

    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def referral_link(self):
        """
        Generate a referral link for the user
        """
        return f"{settings.BASE_URL}/?ref={self.referral_code}"

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
    """
    Referral model to track who referred whom.
    """

    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals"
    )
    referred = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="referral"
    )

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
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    class PayoutType(models.TextChoices):
        BANK = "bank", "Bank"
        CRYPTO = "crypto", "Crypto"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status, default=Status.PENDING)
    payout_type = models.CharField(max_length=10, choices=PayoutType)
    payout_destination = models.CharField(max_length=255)

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
    stripe_subscription_id = models.CharField(max_length=255)

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
        return f"{self.user.username} - {self.status} - {self.frequency}"
