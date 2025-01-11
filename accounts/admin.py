from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User, UserBalance


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
        "created_at",
    ]
    list_filter = ["created_at"]
    inlines = [UserBalanceInline]
    search_fields = ["username", "email"]

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
