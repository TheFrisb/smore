from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from solo.admin import SingletonModelAdmin

from core.models import (
    Prediction,
    PickOfTheDay,
    Product,
    Addon,
    FrequentlyAskedQuestion,
    SiteSettings,
)


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("name", "analysis_per_month", "stripe_product_id"),
            },
        ),
        (
            "Monthly Pricing",
            {
                "fields": ("monthly_price", "monthly_price_stripe_id"),
            },
        ),
        (
            "Yearly Pricing",
            {
                "fields": ("yearly_price", "yearly_price_stripe_id"),
            },
        ),
    )
    list_display = (
        "name",
        "analysis_per_month",
        "monthly_price",
        "yearly_price",
        "order",
    )
    ordering = ["order"]


@admin.register(Addon)
class AddonAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "monthly_price", "yearly_price", "order"]
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


@admin.register(FrequentlyAskedQuestion)
class FrequentlyAskedQuestionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["question", "order"]


admin.site.register(SiteSettings, SingletonModelAdmin)
