import re
from html import unescape

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import strip_tags

from accounts.models import User
from notifications.models import NotificationRequest, UserNotification
from notifications.services.fcm_service import FCMService


def extract_first_30_words(html_content):
    """
    Extract the first 30 words from HTML content by stripping tags and unescaping entities
    """
    if not html_content:
        return ""

    text = strip_tags(html_content)
    text = unescape(text)
    words = re.findall(r"\b\w+\b", text)
    first_30_words = words[:30]
    return " ".join(first_30_words)


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

    if instance.preview and instance.preview.strip():
        # Use preview if available
        body = instance.preview
    else:
        # Extract first 30 words from HTML message
        body = extract_first_30_words(instance.message)

    if instance.user and instance.user.fcm_token:
        # Targeted notification to single user
        response = fcm_service.send_notification(
            title=instance.title,
            body=body,
            data=serialized_data,
            token=instance.user.fcm_token,
        )

        if response.get("status") == "success":
            UserNotification.objects.create(
                request=instance,
                user=instance.user,
                title=instance.title,
                message=instance.message,
                topic=instance.topic,
                icon=instance.icon,
                is_important=instance.is_important,
                is_visible=True,
            )
    else:
        # Broadcast to topic
        response = fcm_service.send_notification(
            title=instance.title,
            body=body,
            data=serialized_data,
            topic=instance.topic.name,
        )

        if response.get("status") == "success":
            users = User.objects.filter(fcm_token__isnull=False)
            UserNotification.objects.bulk_create(
                [
                    UserNotification(
                        request=instance,
                        user=user,
                        title=instance.title,
                        message=instance.message,
                        topic=instance.topic,
                        icon=instance.icon,
                        is_important=instance.is_important,
                        is_visible=True,
                    )
                    for user in users
                ]
            )
