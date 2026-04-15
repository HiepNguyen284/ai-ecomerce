from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'user_id', 'amount', 'method', 'status', 'transaction_id', 'created_at']
    list_filter = ['method', 'status', 'created_at']
    search_fields = ['id', 'order_id', 'user_id', 'transaction_id']
    ordering = ['-created_at']
