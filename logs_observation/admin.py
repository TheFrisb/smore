from django.contrib import admin

from logs_observation.models import Log


# Register your models here.
@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "level", "message")
    search_fields = ("message",)
    list_filter = ("level", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
