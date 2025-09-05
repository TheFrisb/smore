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


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "topic",
        "icon",
        "is_important",
        "is_read",
        "created_at",
    )
    search_fields = ("title", "message", "user__username", "topic__name", "icon")
    list_filter = ("is_read", "is_important", "topic", "created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
