from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from solo.admin import SingletonModelAdmin

from core.models import Product, Addon, Prediction, PickOfTheDay


# Register your models here.
@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "monthly_price", "annual_price", "order"]
    search_fields = ["name"]


@admin.register(Addon)
class AddonAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "monthly_price", "annual_price", "order"]
    search_fields = ["name"]


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "home_team",
        "away_team",
        "prediction",
        "kickoff_time",
        "status",
        "visibility",
    ]
    search_fields = ("home_team", "away_team", "league", "product__name", "prediction")
    list_filter = ["product", "status", "visibility"]
    autocomplete_fields = ["product"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Match Details",
            {
                "fields": (
                    "product",
                    "kickoff_date",
                    "kickoff_time",
                    "league",
                    "home_team",
                    "away_team",
                )
            },
        ),
        ("Prediction Details", {"fields": ("prediction", "odds", "result")}),
        ("Status and Visibility", {"fields": ("status", "visibility")}),
        ("Additional Information", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PickOfTheDay)
class PickOfTheDayAdmin(SingletonModelAdmin):
    autocomplete_fields = ["prediction"]
