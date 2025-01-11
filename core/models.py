from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class BaseInternalModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseProductModel(BaseInternalModel):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return self.name


class Product(BaseProductModel):
    analysis_per_month = models.CharField(max_length=7)


class Addon(BaseProductModel):
    pass
