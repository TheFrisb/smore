from django.db import models

from accounts.models import User
from core.models import BaseInternalModel


# Create your models here.
class Log(BaseInternalModel):
    """
    Model to store logs for observation purposes.
    """
 
    class Level(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"
        CRITICAL = "CRITICAL", "Critical"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="logs",
        verbose_name="User",
        help_text="The user associated with this log entry.",
        null=True,
        blank=True,
    )
    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        default=Level.INFO,
        verbose_name="Log Level",
        help_text="The severity level of the log entry.",
    )
    message = models.JSONField(
        verbose_name="Log Message",
        help_text="The log message, stored as a JSON object.",
        default=dict,
        blank=True,
    )
