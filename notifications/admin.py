import logging

from django.contrib import admin, messages

from notifications.models import (
    NotificationRequest,
    NotificationTopic,
    UserNotification,
)
from notifications.services.fcm_service import FCMService

logger = logging.getLogger(__name__)


# Register your models here.
@admin.register(NotificationTopic)
class NotificationTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(NotificationRequest)
class NotificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "topic",
        "user",
        "icon",
        "is_important",
        "created_at",
        "updated_at",
    )
    search_fields = ("title", "message", "topic__name", "user__username", "icon")
    list_filter = ("topic", "icon", "is_important", "created_at", "updated_at")
    ordering = ("-created_at",)
    autocomplete_fields = ["user"]

    fieldsets = (
        (
            "General Information",
            {
                "fields": ("topic", "user", "is_important"),
            },
        ),
        (
            "Headline",
            {
                "fields": ("icon", "title", "preview"),
            },
        ),
        (
            "Message",
            {
                "fields": ("message",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def _hide_related_notifications(self, request, notification_requests):
        """Helper to hide related UserNotifications for single or bulk deletes."""
        if not notification_requests:  # Handle empty queryset
            logger.info(
                "No NotificationRequests provided for hiding related notifications."
            )
            return
        try:
            # Use a single query to update all related UserNotifications
            logger.info(
                f"Hiding related notifications for NotificationRequests: {notification_requests}"
            )
            UserNotification.objects.filter(request__in=notification_requests).update(
                is_visible=False
            )

            fcm_result = FCMService().send_silent_notification()
            if fcm_result["status"] == "success":
                logger.info("Refetch data message sent successfully to 'ALL' topic")
            else:
                logger.warning(
                    f"Failed to send refetch message: {fcm_result['message']}"
                )
        except Exception as e:
            # Log error or notify admin (optional, adjust based on your needs)
            self.message_user(
                request,
                f"Error hiding related notifications: {str(e)}",
                level=messages.ERROR,
            )

    def delete_queryset(self, request, queryset):
        """Handle bulk deletion in admin."""
        self._hide_related_notifications(request, queryset)

        super().delete_queryset(request, queryset)

    def delete_model(self, request, obj):
        """Handle single object deletion in admin."""
        # Pass as a single-item queryset for consistency
        self._hide_related_notifications(request, [obj])

        super().delete_model(request, obj)

    class Media:
        css = {"all": ("css/admin/custom_admin.css",)}


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "topic",
        "icon",
        "is_important",
        "is_visible",
        "is_read",
        "created_at",
    )
    search_fields = ("title", "message", "user__username", "topic__name", "icon")
    list_filter = ("is_read", "is_important", "topic", "created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
