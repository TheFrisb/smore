from django.contrib import admin

from notifications.models import (
    UserNotification,
    NotificationRequest,
    NotificationTopic,
)


# Register your models here.
@admin.register(NotificationTopic)
class NotificationTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(NotificationRequest)
class NotificationRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "created_at", "updated_at")
    search_fields = ("title", "message", "topic__name")
    list_filter = ("topic", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "topic", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "topic__name")
    list_filter = ("is_read", "topic", "created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
