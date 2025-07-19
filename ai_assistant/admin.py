from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from ai_assistant.models import Message, SuggestedMessage


# Register your models here.
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message", "direction", "user", "created_at")
    list_filter = ("direction", "user")
    search_fields = ("message", "user__username")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(SuggestedMessage)
class SuggestedMessageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("primary_text", "order")
    search_fields = ("primary_text",)
    date_hierarchy = "created_at"
