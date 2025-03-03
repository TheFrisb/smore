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
