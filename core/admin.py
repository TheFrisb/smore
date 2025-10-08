import logging
from datetime import timedelta

from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Min, Q, Value
from django.db.models.functions import Greatest, Lower
from django.utils import timezone
from solo.admin import SingletonModelAdmin

from accounts.models import PurchasedPredictions, PurchasedTickets
from core.models import (
    BetLine,
    FrequentlyAskedQuestion,
    PickOfTheDay,
    Prediction,
    SiteSettings,
    SportCountry,
    SportLeague,
    SportMatch,
    SportTeam,
    TeamStanding,
    Ticket,
    OldProduct,
)
from subscriptions.models import Product

logger = logging.getLogger(__name__)


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
        ("Stake Information", {"fields": ["stake"]}),
        ("Status and Visibility", {"fields": ("status", "visibility")}),
        ("Additional Information", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.exclude(id=1024)

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


@admin.register(SportLeague)
class SportLeagueAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "product", "type"]


@admin.register(SportTeam)
class SportTeamAdmin(admin.ModelAdmin):
    search_fields = ["name", "league__name"]
    list_display = ["name", "product", "type"]


@admin.register(SportMatch)
class SportMatchAdmin(admin.ModelAdmin):
    search_fields = [
        "home_team__name",
        "away_team__name",
        "league__name",
        "kickoff_datetime",
    ]

    list_display = [
        "home_team",
        "away_team",
        "product",
        "type",
    ]

    readonly_fields = ["home_team", "away_team", "league"]

    ordering = ["-kickoff_datetime"]

    def get_search_results(self, request, queryset, search_term):
        # Only apply custom trigram logic when our JS autocomplete ‘term’ param is present
        if "term" in request.GET:
            # 1) apply your date window
            midnight_today = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_date = midnight_today - timedelta(days=2)
            queryset = queryset.filter(kickoff_datetime__gte=start_date)

            # 2) apply your existing product filter
            product_id = request.GET.get("product_id")
            if product_id:
                queryset = queryset.filter(product_id=product_id)

            # 3) annotate three separate trigram similarities
            qs = queryset.annotate(
                home_sim=TrigramSimilarity(
                    Lower(Unaccent("home_team__name")),
                    Lower(Unaccent(Value(search_term))),
                ),
                away_sim=TrigramSimilarity(
                    Lower(Unaccent("away_team__name")),
                    Lower(Unaccent(Value(search_term))),
                ),
                league_sim=TrigramSimilarity(
                    Lower(Unaccent("league__name")), Lower(Unaccent(Value(search_term)))
                ),
            )

            # 4) filter to only “reasonably similar” matches
            qs = qs.filter(
                Q(home_sim__gt=0.3) | Q(away_sim__gt=0.3) | Q(league_sim__gt=0.3)
            )

            # 5) order by the greatest of the three
            qs = qs.annotate(
                best_sim=Greatest("home_sim", "away_sim", "league_sim")
            ).order_by("-best_sim")

            # 6) finally pass this into the default admin search handling
            return super().get_search_results(request, qs, search_term)

        # Fallback: exactly as before
        return super().get_search_results(request, queryset, search_term)


# Inline admin for TicketMatch
class BetLineInline(admin.TabularInline):
    model = BetLine
    autocomplete_fields = ["match"]
    fields = ["match", "bet", "bet_type", "odds", "status"]
    extra = 6


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    inlines = [BetLineInline]
    list_display = ["__str__", "starts_at", "visibility", "status_display"]
    list_filter = ["product", "status", "visibility"]
    ordering = ["-starts_at"]
    readonly_fields = ["created_at", "updated_at", "starts_at", "label"]
    fieldsets = (
        (
            "Ticket Details",
            {
                "fields": ("product", "status", "visibility", "label", "stake"),
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("created_at", "updated_at", "starts_at"),
            },
        ),
    )

    def status_display(self, obj):
        if obj.status == Ticket.Status.WON:
            return True
        elif obj.status == Ticket.Status.LOST:
            return False
        else:
            return None

    status_display.boolean = True
    status_display.short_description = "Status"
    status_display.admin_order_field = "status"

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        ticket = form.instance
        earliest_datetime = ticket.bet_lines.aggregate(Min("match__kickoff_datetime"))[
            "match__kickoff_datetime__min"
        ]
        ticket.starts_at = earliest_datetime
        ticket.save()

        products = Product.objects.all()
        for product in products:
            pending_tickets = Ticket.objects.filter(
                status=Ticket.Status.PENDING, product=product
            ).order_by("product__name", "starts_at")

            for i, t in enumerate(pending_tickets, start=1):
                t.label = f"Premium Parlay #{i}"
                t.save()

    class Media:
        css = {"all": ("css/admin/custom_admin.css",)}
        js = (
            "admin/js/vendor/jquery/jquery.js",
            "admin/js/jquery.init.js",
            "js/admin/ticket_admin.js",
        )


admin.site.register(SiteSettings, SingletonModelAdmin)
admin.site.register(SportCountry)
admin.site.register(PurchasedPredictions)
admin.site.register(PurchasedTickets)
admin.site.register(TeamStanding)
admin.site.register(OldProduct)
