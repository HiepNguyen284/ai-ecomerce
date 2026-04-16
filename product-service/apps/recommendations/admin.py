from django.contrib import admin
from .models import ProductView, CategoryPreference


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'product', 'category', 'viewed_at']
    list_filter = ['category', 'viewed_at']
    search_fields = ['session_id', 'product__name']
    readonly_fields = ['id', 'viewed_at']


@admin.register(CategoryPreference)
class CategoryPreferenceAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'category', 'view_count', 'score', 'last_viewed']
    list_filter = ['category']
    search_fields = ['session_id']
    readonly_fields = ['id', 'updated_at']
