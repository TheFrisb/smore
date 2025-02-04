from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel


# Create your models here.
class BaseInternalModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseProductModel(BaseInternalModel):
    stripe_product_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_price_stripe_id = models.CharField(max_length=255)

    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price_stripe_id = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return self.name


class Product(BaseProductModel):
    analysis_per_month = models.CharField(max_length=12)


class Addon(BaseProductModel):
    description = models.TextField()


class Prediction(BaseInternalModel):
    class Status(models.TextChoices):
        WON = "WON", _("Won")
        LOST = "LOST", _("Lost")
        PENDING = "PENDING", _("Pending")

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    visibility = models.CharField(
        max_length=10, choices=Visibility, default=Visibility.PUBLIC, db_index=True
    )
    home_team = models.CharField(max_length=255)
    away_team = models.CharField(max_length=255)
    prediction = models.CharField(max_length=255)
    odds = models.DecimalField(max_digits=10, decimal_places=2)
    result = models.CharField(max_length=255, blank=True)
    kickoff_date = models.DateField()
    kickoff_time = models.TimeField()
    league = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10, choices=Status, default=Status.PENDING, db_index=True
    )

    def __str__(self):
        return f"{self.product.name} prediction for {self.home_team} vs {self.away_team}, {self.kickoff_time} ({self.league})"

    @property
    def kickoff_datetime(self):
        # return date and time in a single string without time having seconds
        return f"{self.kickoff_date} {self.kickoff_time.strftime('%H:%M')} (GMT+1)"

    class Meta:
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"


class PickOfTheDay(BaseInternalModel, SingletonModel):
    prediction = models.OneToOneField(
        Prediction, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"Pick of the Day: {self.prediction}"


class FrequentlyAskedQuestion(BaseInternalModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ["order"]


class SiteSettings(BaseInternalModel, SingletonModel):
    customer_withdrawal_request_template_id = models.IntegerField(blank=True, null=True)
    email_confirmation_template_id = models.IntegerField(blank=True, null=True)
    password_reset_template_id = models.IntegerField(blank=True, null=True)
    generic_content_template_id = models.IntegerField(blank=True, null=True)
    notification_email = models.EmailField()

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
