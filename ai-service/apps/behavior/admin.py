from django.contrib import admin
from .models import UserBehavior


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'product_id', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user_id', 'product_id']
    ordering = ['-timestamp']
