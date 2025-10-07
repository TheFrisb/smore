from django.contrib.admin import SimpleListFilter
from django.db.models import Q

from subscriptions.models import UserSubscription, BillingProvider


class UserSubscriptionTypeFilter(SimpleListFilter):
    title = "Subscription Type"
    parameter_name = "subscription_type"

    def lookups(self, request, model_admin):
        return (
            ("paid", "Paid Subscription"),
            ("custom", "Customer (internal)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "paid":
            return (
                queryset.filter(subscriptions__is_active=True)
                .filter(~Q(subscriptions__provider=BillingProvider.INTERNAL))
                .distinct()
            )

        if self.value() == "custom":
            return (
                queryset.filter(subscriptions__is_active=True)
                .filter(subscriptions__provider=BillingProvider.INTERNAL)
                .distinct()
            )

        return queryset


class UserActiveStatusFilter(SimpleListFilter):
    """Filter users based on whether they have at least one active subscription."""

    title = "Subscription Status"
    parameter_name = "active_status"

    def lookups(self, request, model_admin):
        return (
            ("active", "Active Subscription"),
            ("inactive", "Inactive Subscription"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(subscriptions__is_active=True).distinct()
        if self.value() == "inactive":
            return queryset.exclude(subscriptions__is_active=True)
        return queryset
