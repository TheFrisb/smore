from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from core.models import BaseInternalModel


# Create your models here.
class NotificationTopic(BaseInternalModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Notification Topic"
        verbose_name_plural = "Notification Topics"

    def __str__(self):
        return self.name


class NotificationRequest(BaseInternalModel):
    class IconNames(models.TextChoices):
        SOCCER = "SOCCER", "Soccer"
        BASKETBALL = "BASKETBALL", "Basketball"
        TROPHY = "TROPHY", "Trophy"
        CHECKMARK = "CHECKMARK", "Checkmark"
        XMARK = "XMARK", "X Mark"

    topic = models.ForeignKey(
        NotificationTopic, on_delete=models.CASCADE, related_name="requests"
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notification_requests",
        null=True,
        blank=True,
    )
    icon = models.CharField(
        max_length=20,
        choices=IconNames.choices,
        default=None,
        blank=True,
        null=True,
    )
    is_important = models.BooleanField(default=False)

    title = models.CharField(max_length=255)
    preview = models.CharField(max_length=512, blank=True, null=True)
    message = CKEditor5Field(blank=True)

    class Meta:
        verbose_name = "Notification Request"
        verbose_name_plural = "Notification Requests"

    def __str__(self):
        return f"{self.title} ({self.topic.name})"


class UserNotification(BaseInternalModel):
    class IconNames(models.TextChoices):
        SOCCER = "SOCCER", "Soccer"
        BASKETBALL = "BASKETBALL", "Basketball"
        TROPHY = "TROPHY", "Trophy"
        CHECKMARK = "CHECKMARK", "Checkmark"
        XMARK = "XMARK", "X Mark"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    topic = models.ForeignKey(
        NotificationTopic,
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_notifications",
    )
    icon = models.CharField(
        max_length=20,
        choices=IconNames.choices,
        default=IconNames.TROPHY,
        blank=True,
        null=True,
    )
    is_important = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
