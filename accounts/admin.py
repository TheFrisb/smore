from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, F, Q, Value
from django.db.models.functions import Coalesce
from django.utils import dateformat
from django.utils.translation import gettext_lazy as _

from accounts.admin_filters import (
    UserActiveStatusFilter,
    UserSubscriptionTypeFilter,
)
from accounts.models import *
from accounts.services.referral_service import ReferralService


# Register your models here.
@admin.register(User)
class UserAdmin(UserAdmin):
    change_form_template = "admin/accounts/user/change_form.html"
    search_fields = [
        "username",
        "email",
        "stripe_customer_id",
        "first_name",
        "last_name",
    ]
    ordering = ["-created_at"]
    list_filter = [UserActiveStatusFilter, UserSubscriptionTypeFilter]
    list_display = [
        "username",
        "email",
        "direct_referrals",
        "indirect_referrals",
        "available_balance",
        "subscribed_sports",
        "subscription_start_date",
        "subscription_end_date",
        "is_subscribed",
        "is_custom_subscription",
        "created_at",
    ]

    fieldsets = (
        (None, {"fields": ("username", "password", "provider", "google_sub")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "referral_link",
                    "stripe_customer_id",
                    "fcm_token",
                )
            },
        ),
        (
            _("Referrals and Balance"),
            {
                "fields": (
                    "direct_referrals",
                    "indirect_referrals",
                    "available_balance",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    readonly_fields = [
        "created_at",
        "updated_at",
        "referral_link",
        "available_balance",
        "direct_referrals",
        "indirect_referrals",
        "provider",
        "google_sub",
    ]

    def get_queryset(self, request):
        """
        Annotate direct and indirect referrals for efficient querying.
        """
        queryset = super().get_queryset(request)
        return queryset.annotate(
            direct_referral_count=Count(
                "referrals", filter=Q(referrals__level=Referral.Level.DIRECT)
            ),
            indirect_referral_count=Count(
                "referrals", filter=Q(referrals__level=Referral.Level.INDIRECT)
            ),
            balance_annotation=Coalesce(F("balance__balance"), Value(Decimal("0.00"))),
        )

    def direct_referrals(self, obj):
        """
        Return the count of direct referrals for a user.
        """
        return obj.direct_referral_count

    def indirect_referrals(self, obj):
        """
        Return the count of indirect referrals for a user.
        """
        return obj.indirect_referral_count

    def available_balance(self, obj):
        """
        Display the available balance for a user from the annotated field.
        """
        return obj.balance_annotation

    def subscription_start_date(self, obj):
        """
        Display the subscription start date if it exists.
        """
        if hasattr(obj, "subscription") and obj.subscription:
            return dateformat.format(obj.subscription.start_date, "F j, Y")
        return None

    def subscription_end_date(self, obj):
        """
        Display the subscription end date if it exists.
        """
        if hasattr(obj, "subscription") and obj.subscription:
            return dateformat.format(obj.subscription.end_date, "F j, Y")
        return None

    def is_subscribed(self, obj):
        """
        Display whether the user is subscribed (Active).
        """
        return obj.has_active_subscription

    def is_custom_subscription(self, obj):
        if hasattr(obj, "subscription") and obj.subscription:
            return not obj.subscription.stripe_subscription_id
        return False

    def subscribed_sports(self, obj):
        """
        Return a comma-separated list of subscribed sports (products) for the user.
        """
        if hasattr(obj, "subscription") and obj.subscription:
            return ", ".join(
                [product.name for product in obj.subscription.products.all()]
            )
        return None

    direct_referrals.admin_order_field = "direct_referral_count"
    direct_referrals.short_description = "Direct Referrals"

    indirect_referrals.admin_order_field = "indirect_referral_count"
    indirect_referrals.short_description = "Indirect Referrals"

    available_balance.admin_order_field = "balance_annotation"
    available_balance.short_description = "Available Balance"

    subscription_start_date.short_description = "Subscription Start"
    subscription_end_date.short_description = "Subscription End"

    is_subscribed.boolean = True
    is_subscribed.short_description = "Subscribed"

    is_custom_subscription.boolean = True
    is_custom_subscription.short_description = "Custom Subscription"

    subscribed_sports.short_description = "Subscribed Sports"
    #
    # def get_inlines(self, request, obj):
    #     if hasattr(obj, "subscription") and obj.subscription:
    #         return [UserSubscriptionInline]
    #     return []

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}

        # Get the User object
        user = self.get_object(request, object_id)
        # or user = get_object_or_404(User, pk=object_id) if you prefer that approach

        # Build the network data using your ReferralService
        referral_service = ReferralService()
        network_data = referral_service.build_network(user)

        # Inject the network data into the context
        extra_context["network"] = network_data

        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "payout_type", "created_at")
    list_filter = ("status", "payout_type", "created_at")
    search_fields = (
        "user__username",
        "full_name",
        "email",
        "iban",
        "cryptocurrency_address",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def get_general_fieldset(self):
        """Returns the general fieldset, always included."""
        return (
            "General Information",
            {
                "fields": (
                    "user",
                    "amount",
                    "status",
                    "payout_type",
                    "created_at",
                    "updated_at",
                )
            },
        )

    def get_all_details_fieldset(self):
        """Returns the full details fieldset for adding a new withdrawal request."""
        return (
            "All Details",
            {
                "fields": (
                    "full_name",
                    "email",
                    "iban",
                    "country",
                    "cryptocurrency_address",
                )
            },
        )

    def get_cryptocurrency_fieldset(self):
        """Returns the Cryptocurrency-specific fieldset."""
        return (
            "Cryptocurrency Details",
            {"fields": ("cryptocurrency_address",)},
        )

    def get_bank_fieldset(self):
        """Returns the Bank-specific fieldset."""
        return (
            "Bank Details",
            {"fields": ("full_name", "email", "iban", "country")},
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = [self.get_general_fieldset()]

        if obj is None:
            fieldsets.append(self.get_all_details_fieldset())
        else:
            # Adjust fieldsets based on payout_type

            if obj.payout_type == WithdrawalRequest.PayoutType.CRYPTOCURRENCY:
                fieldsets.append(self.get_cryptocurrency_fieldset())
            elif obj.payout_type == WithdrawalRequest.PayoutType.BANK:
                fieldsets.append(self.get_bank_fieldset())

        return fieldsets


class ReferralEarningInline(admin.TabularInline):
    model = ReferralEarning
    autocomplete_fields = ["referral", "receiver"]
    extra = 1


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    autocomplete_fields = ["referrer", "referred"]
    search_fields = ["referrer__username", "referred__username"]
    inlines = [ReferralEarningInline]


@admin.register(PurchasedDailyOffer)
class PurchasedDailyOfferAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "for_date")
