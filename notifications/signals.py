from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from notifications.models import NotificationRequest, UserNotification
from notifications.service import FCMService


@receiver(post_save, sender=NotificationRequest)
def handle_notification_request(sender, instance, created, **kwargs):
    """
    Handle new NotificationRequest: send FCM notification and create UserNotifications.
    If a specific user is set, send only to that user's token and create a single UserNotification.
    Otherwise, send to the topic and create UserNotifications for all users with FCM tokens.
    """
    if not created:
        return

    fcm_service = FCMService()
    # serialized_data = NotificationRequestSerializer(instance).data
    serialized_data = {}

    if instance.user and instance.user.fcm_token:
        # Targeted notification to single user
        response = fcm_service.send_notification(
            title=instance.title,
            body=instance.preview,
            data=serialized_data,
            token=instance.user.fcm_token,
        )

        if response.get("status") == "success":
            UserNotification.objects.create(
                user=instance.user,
                title=instance.title,
                message=instance.message,
                topic=instance.topic,
                icon=instance.icon,
                is_important=instance.is_important,
            )
    else:
        # Broadcast to topic
        response = fcm_service.send_notification(
            title=instance.title,
            body=instance.preview,
            data=serialized_data,
            topic=instance.topic.name,
        )

        if response.get("status") == "success":
            users = User.objects.filter(fcm_token__isnull=False)
            UserNotification.objects.bulk_create(
                [
                    UserNotification(
                        user=user,
                        title=instance.title,
                        message=instance.message,
                        topic=instance.topic,
                        icon=instance.icon,
                        is_important=instance.is_important,
                    )
                    for user in users
                ]
            )
