from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import *


class UserBalanceInline(admin.TabularInline):
    """
    Inline for UserBalance model in User admin.
    """

    model = UserBalance
    fields = ["balance"]
    readonly_fields = ["balance"]
    extra = 0


# Register your models here.
@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Admin model for User model.
    """

    list_display = [
        "username",
        "email",
        "total_balance",
        "first_level_referrals_count",
        "second_level_referrals_count",
        "stripe_customer_id",
        "created_at",
    ]
    list_filter = ["created_at"]
    inlines = [UserBalanceInline]
    search_fields = ["username", "email"]

    def get_ordering(self, request):
        return ["-created_at"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related(
            "referrals",
            "referrals__referred__referrals",
        )
        return queryset

    def total_balance(self, obj: User):
        return obj.balance.balance

    def first_level_referrals_count(self, obj: User):
        return obj.referrals.count()

    def second_level_referrals_count(self, obj: User):
        return sum(
            referral.referred.referrals.count() for referral in obj.referrals.all()
        )

    total_balance.short_description = "Total Balance"
    first_level_referrals_count.short_description = "1st-Level Referrals"
    second_level_referrals_count.short_description = "2nd-Level Referrals"


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
                    "payoneer_customer_id",
                    "iban",
                    "country",
                    "cryptocurrency_address",
                )
            },
        )

    def get_payoneer_fieldset(self):
        """Returns the Payoneer-specific fieldset."""
        return (
            "Payoneer Details",
            {"fields": ("full_name", "email", "payoneer_customer_id")},
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
            if obj.payout_type == WithdrawalRequest.PayoutType.PAYONEER:
                fieldsets.append(self.get_payoneer_fieldset())
            elif obj.payout_type == WithdrawalRequest.PayoutType.CRYPTOCURRENCY:
                fieldsets.append(self.get_cryptocurrency_fieldset())
            elif obj.payout_type == WithdrawalRequest.PayoutType.BANK:
                fieldsets.append(self.get_bank_fieldset())

        return fieldsets


admin.site.register(UserSubscription)
