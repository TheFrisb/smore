from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from core.models import Product


# Register your models here.
@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "price", "discounted_price"]
    search_fields = ["name"]

    sortable = "order"
