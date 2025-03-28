import logging
from datetime import timedelta

from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin
from django.utils import timezone
from solo.admin import SingletonModelAdmin

from core.models import (
    Prediction,
    PickOfTheDay,
    Product,
    FrequentlyAskedQuestion,
    SiteSettings,
    SportCountry,
    SportLeague,
    SportTeam,
    SportMatch,
)

logger = logging.getLogger(__name__)


# Register your models here.
@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("name", "type", "analysis_per_month", "stripe_product_id"),
            },
        ),
        (
            "Monthly Pricing",
            {
                "fields": ("monthly_price", "monthly_price_stripe_id"),
            },
        ),
        (
            "Discounted Monthly Pricing",
            {
                "fields": (
                    "discounted_monthly_price",
                    "discounted_monthly_price_stripe_id",
                ),
            },
        ),
        (
            "Yearly Pricing",
            {
                "fields": ("yearly_price", "yearly_price_stripe_id"),
            },
        ),
        (
            "Discounted Yearly Pricing",
            {
                "fields": (
                    "discounted_yearly_price",
                    "discounted_yearly_price_stripe_id",
                ),
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("description",),
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


class PredictionAdminForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = "__all__"


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    form = PredictionAdminForm
    autocomplete_fields = ["match"]
    list_display = [
        "match",
        "product",
        "status",
        "visibility",
        "detailed_analysis_status",
    ]

    search_fields = ("match__home_team__name", "match__away_team__name")
    list_filter = ["product", "status", "visibility"]
    ordering = ["-match__kickoff_datetime"]
    readonly_fields = ["created_at", "updated_at", "result"]

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

    def get_result(self, obj):
        return obj.result

    def detailed_analysis_status(self, obj):
        return obj.has_detailed_analysis

    detailed_analysis_status.boolean = True
    detailed_analysis_status.short_description = "Detailed Analysis"

    class Media:
        css = {"all": ("css/admin/custom_admin.css",)}
        js = (
            "admin/js/vendor/jquery/jquery.js",
            "admin/js/jquery.init.js",
            "js/admin/prediction_admin.js",
        )


@admin.register(PickOfTheDay)
class PickOfTheDayAdmin(SingletonModelAdmin):
    autocomplete_fields = ["prediction"]


@admin.register(FrequentlyAskedQuestion)
class FrequentlyAskedQuestionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["question", "order"]


admin.site.register(SiteSettings, SingletonModelAdmin)
admin.site.register(SportCountry)


@admin.register(SportLeague)
class SportLeagueAdmin(admin.ModelAdmin):
    search_fields = ["name"]


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

    readonly_fields = ["home_team", "away_team", "league"]

    ordering = ["-kickoff_datetime"]

    def get_search_results(self, request, queryset, search_term):
        if "term" not in request.GET:
            return super().get_search_results(request, queryset, search_term)

        midnight_today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_date = midnight_today - timedelta(days=2)
        queryset = queryset.filter(kickoff_datetime__gte=start_date)

        product_id = request.GET.get("product_id")

        if product_id:
            product = Product.objects.filter(id=product_id).first()
            if product:
                queryset = queryset.filter(product=product)

        return super().get_search_results(request, queryset, search_term)
