from rest_framework import serializers
from .models import UserBehavior


class UserBehaviorSerializer(serializers.ModelSerializer):
    """Serializer for UserBehavior model."""

    class Meta:
        model = UserBehavior
        fields = ['id', 'user_id', 'product_id', 'action', 'timestamp']
        read_only_fields = ['id']


class BehaviorStatsSerializer(serializers.Serializer):
    """Serializer for aggregated behavior statistics."""
    action = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class UserSummarySerializer(serializers.Serializer):
    """Serializer for per-user behavior summary."""
    user_id = serializers.CharField(max_length=36)
    total_actions = serializers.IntegerField()
    unique_products = serializers.IntegerField()
    actions_breakdown = serializers.DictField(child=serializers.IntegerField())
    first_activity = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()


class DatasetInfoSerializer(serializers.Serializer):
    """Serializer for dataset metadata."""
    total_records = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_products = serializers.IntegerField()
    action_types = serializers.ListField(child=serializers.CharField())
    action_distribution = serializers.DictField(child=serializers.IntegerField())
    date_range = serializers.DictField()
    csv_path = serializers.CharField()
