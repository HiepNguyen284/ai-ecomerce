from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_id', 'product_name', 'product_price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user_id', 'shipping_name']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
