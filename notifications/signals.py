from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from notifications.models import NotificationRequest, UserNotification
from notifications.service import FCMService


@receiver(post_save, sender=NotificationRequest)
def handle_notification_request(sender, instance, created, **kwargs):
    """
    Handle new NotificationRequest: send FCM notification and create UserNotifications.
    """
    if not created:
        return

    fcm_service = FCMService()
    response = fcm_service.send_notification(
        topic=instance.topic.name, title=instance.title, body=instance.message
    )

    # Create UserNotifications for all users subscribed to the topic
    if response.get("status") == "success":
        users = User.objects.filter(fcm_token__isnull=False)

        UserNotification.objects.bulk_create(
            [
                UserNotification(
                    user=user,
                    title=instance.title,
                    message=instance.message,
                    topic=instance.topic,
                )
                for user in users
            ]
        )
