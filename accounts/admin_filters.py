from django.contrib.admin import SimpleListFilter
from django.db.models import Q

from accounts.models import UserSubscription


class SubscriptionTypeFilter(SimpleListFilter):
    title = "Subscription Type"
    parameter_name = "subscription_type"

    def lookups(self, request, model_admin):
        return (
            ("paid", "Paid"),
            ("custom", "Custom"),
        )

    def queryset(self, request, queryset):
        if self.value() == "paid":
            return queryset.exclude(stripe_subscription_id="")
        if self.value() == "custom":
            return queryset.filter(stripe_subscription_id="")
        return queryset


class UserSubscriptionTypeFilter(SimpleListFilter):
    title = "Subscription Type"
    parameter_name = "subscription_type"

    def lookups(self, request, model_admin):
        return (
            ("paid", "Paid Subscription"),
            ("custom", "Custom Subscription"),
        )

    def queryset(self, request, queryset):
        if self.value() == "paid":
            return queryset.exclude(subscription__stripe_subscription_id="")
        if self.value() == "custom":
            return queryset.filter(subscription__stripe_subscription_id="")
        return queryset


class UserActiveStatusFilter(SimpleListFilter):
    """Filter users based on their subscription status (Active/Inactive)."""

    title = "Subscription Status"
    parameter_name = "active_status"

    def lookups(self, request, model_admin):
        return (
            ("active", "Active Subscription"),
            ("inactive", "Inactive Subscription"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(subscription__status=UserSubscription.Status.ACTIVE)
        if self.value() == "inactive":
            # Filter users with an inactive subscription or no subscription
            return queryset.filter(
                Q(subscription__status=UserSubscription.Status.INACTIVE)
                | Q(subscription__isnull=True)
            )
        return queryset
