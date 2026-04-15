from rest_framework import serializers
from apps.products.serializers import ProductListSerializer
from .models import ProductView, CategoryPreference


class TrackViewSerializer(serializers.Serializer):
    """Serializer for tracking product view events."""
    product_id = serializers.UUIDField(required=True)
    session_id = serializers.CharField(max_length=100, required=True)


class CategoryPreferenceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = CategoryPreference
        fields = ['category', 'category_name', 'view_count', 'score', 'last_viewed']


class RecommendationResponseSerializer(serializers.Serializer):
    """Response serializer for recommendation endpoint."""
    recommended_products = ProductListSerializer(many=True)
    category_preferences = CategoryPreferenceSerializer(many=True)
    analysis = serializers.DictField()
