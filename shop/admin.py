from django.contrib import admin

from .models import Category, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active")
    list_filter = ("category", "is_active")
    list_editable = ("price", "stock", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "payment_method", "total", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("number", "user__username", "email")
    readonly_fields = ("number", "user", "total", "created_at")
    inlines = (OrderItemInline,)
