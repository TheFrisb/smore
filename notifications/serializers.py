from rest_framework import serializers

from notifications.models import UserNotification, NotificationRequest


class NotificationRequestSerializer(serializers.ModelSerializer):
    topic = serializers.CharField(source="topic.name")
    user = serializers.CharField(source="user.username", allow_null=True)
    image = serializers.ImageField(use_url=True, allow_null=True)

    class Meta:
        model = NotificationRequest
        fields = [
            "id",
            "topic",
            "user",
            "image",
            "icon",
            "is_important",
            "title",
            "message",
            "created_at",
        ]
        read_only_fields = fields


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = [
            "id",
            "user",
            "title",
            "message",
            "is_read",
            "icon",
            "is_important",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "title",
            "message",
            "created_at",
            "user",
            "icon",
            "is_important",
        ]
