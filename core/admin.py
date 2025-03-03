from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin
from django.utils import timezone
from solo.admin import SingletonModelAdmin

from core.models import (
    Prediction,
    PickOfTheDay,
    Product,
    Addon,
    FrequentlyAskedQuestion,
    SiteSettings,
    SportCountry,
    SportLeague,
    SportTeam,
    SportMatch,
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


class PredictionAdminForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Calculate midnight today in UTC
        midnight_today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Filter SportMatch queryset to include only matches on or after today
        self.fields["match"].queryset = SportMatch.objects.filter(
            kickoff_datetime__gte=midnight_today
        )


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    form = PredictionAdminForm
    autocomplete_fields = ["match"]
    list_display = [
        "match",
        "prediction",
        "status",
        "visibility",
    ]
    search_fields = ("match__home_team__name", "match__away_team__name")
    list_filter = ["product", "status", "visibility"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Match Details",
            {
                "fields": (
                    "product",
                    "match",
                ),
            },
        ),
        (
            "Prediction Details",
            {"fields": ("prediction", "odds", "result", "detailed_analysis")},
        ),
        ("Status and Visibility", {"fields": ("status", "visibility")}),
        ("Additional Information", {"fields": ("created_at", "updated_at")}),
    )

    class Media:
        css = {"all": ("css/admin/custom_admin.css",)}


@admin.register(PickOfTheDay)
class PickOfTheDayAdmin(SingletonModelAdmin):
    autocomplete_fields = ["prediction"]


@admin.register(FrequentlyAskedQuestion)
class FrequentlyAskedQuestionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["question", "order"]


admin.site.register(SiteSettings, SingletonModelAdmin)
admin.site.register(SportCountry)
admin.site.register(SportLeague)


@admin.register(SportTeam)
class SportTeamAdmin(admin.ModelAdmin):
    search_fields = ["name", "league__name"]


@admin.register(SportMatch)
class SportMatchAdmin(admin.ModelAdmin):
    search_fields = [
        "home_team__name",
        "away_team__name",
        "league__name",
        "kickoff_datetime",
    ]

    def get_search_results(self, request, queryset, search_term):
        # Filter matches to those on or after midnight today
        midnight_today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        queryset = queryset.filter(kickoff_datetime__gte=midnight_today)
        # Apply the default search filtering
        return super().get_search_results(request, queryset, search_term)
