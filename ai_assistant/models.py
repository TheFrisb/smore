from django.db import models

from core.models import BaseInternalModel


# Create your models here.
class Message(BaseInternalModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound"
        OUTBOUND = "outbound"

    message = models.TextField()
    direction = models.CharField(max_length=10, choices=Direction)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.direction} message for {self.user}"


class SuggestedMessage(BaseInternalModel):
    primary_text = models.CharField(max_length=255)
    secondary_text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    @property
    def query(self):
        return f"{self.primary_text} {self.secondary_text}"

    def __str__(self):
        return self.primary_text

    class Meta:
        ordering = ["order"]
