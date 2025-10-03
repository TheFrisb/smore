from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseInternalModel


class BillingProvider(models.TextChoices):
    STRIPE = "STRIPE", "Stripe"
    REVENUECAT = "REVENUECAT", "RevenueCat"
    INTERNAL = "INTERNAL", "Internal"


class BillingInterval(models.TextChoices):
    WEEK = "WEEK", "Week"
    MONTH = "MONTH", "Month"


class Product(BaseInternalModel):
    class Names(models.TextChoices):
        SOCCER = "Soccer", _("Soccer")
        BASKETBALL = "Basketball", _("Basketball")
        NFL_NHL = "NFL_NHL", _("NFL, NHL")
        TENNIS = "Tennis", _("Tennis")
        AI_ANALYST = "AI Analyst", _("AI Analyst")

    name = models.CharField(
        max_length=50,
        choices=Names.choices,
        unique=True,
        db_index=True,
    )
    analysis_per_month = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order"]


class ProductPrice(BaseInternalModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="prices",
    )
    provider = models.CharField(
        max_length=20,
        choices=BillingProvider.choices,
    )
    provider_price_id = models.CharField(max_length=255)
    currency = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(
        max_length=10,
        choices=BillingInterval.choices,
    )
    interval_count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("provider", "provider_price_id")

    def __str__(self):
        return f"{self.product.name} - {self.currency}{self.amount} every {self.interval_count} {self.interval}(s)"


class UserSubscription(BaseInternalModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    product_price = models.ForeignKey(
        ProductPrice,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
    )
    provider = models.CharField(
        max_length=20,
        choices=BillingProvider.choices,
    )
    provider_subscription_id = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Subscription of {self.user.email} to {self.product_price.product.name}"
