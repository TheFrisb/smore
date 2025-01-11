from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from core.models import Product, Addon


# Register your models here.
@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "price", "discounted_price", "order"]
    search_fields = ["name"]


@admin.register(Addon)
class AddonAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "price", "discounted_price", "order"]
    search_fields = ["name"]
