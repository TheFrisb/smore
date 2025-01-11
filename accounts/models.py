import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import BaseInternalModel


# Create your models here.
class User(BaseInternalModel, AbstractUser):
    """
    Custom User model to store user details.
    """

    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)

    def __str__(self):
        return self.username

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
