from django.db import models

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
    topic = models.ForeignKey(
        NotificationTopic, on_delete=models.CASCADE, related_name="requests"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()

    class Meta:
        verbose_name = "Notification Request"
        verbose_name_plural = "Notification Requests"

    def __str__(self):
        return f"{self.title} ({self.topic.name})"


class UserNotification(BaseInternalModel):
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

    class Meta:
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
