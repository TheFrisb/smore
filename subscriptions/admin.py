# admin.py
from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from .models import PriceCoupon, Product, ProductPrice, UserSubscription


class ProductPriceInline(admin.TabularInline):
    model = ProductPrice
    extra = 0
    fields = (
        "provider",
        "provider_price_id",
        "currency",
        "amount",
        "interval",
        "interval_count",
    )


@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = (ProductPriceInline,)


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "provider",
        "provider_price_id",
        "currency",
        "amount",
        "interval",
        "interval_count",
    )
    list_filter = ("provider", "currency", "interval", "product")
    search_fields = ("provider_price_id", "product__name")
    ordering = ("product__name", "provider")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product_name",
        "provider",
        "is_active",
        "start_date",
        "end_date",
    )
    list_filter = ("provider", "is_active", "product_price__product")
    search_fields = (
        "user__email",
        "user__username",
        "provider_subscription_id",
        "product_price__product__name",
    )
    ordering = ("-start_date",)
    date_hierarchy = "start_date"
    list_select_related = ("product_price", "product_price__product", "user")
    autocomplete_fields = ["user", "product_price"]

    @admin.display(description="Product", ordering="product_price__product__name")
    def product_name(self, obj):
        product = getattr(getattr(obj, "product_price", None), "product", None)
        return getattr(product, "name", "-")


@admin.register(PriceCoupon)
class PriceCouponAdmin(admin.ModelAdmin):
    list_display = ["provider", "provider_coupon_id", "is_active"]
