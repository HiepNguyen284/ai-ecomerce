from rest_framework import serializers
from .models import (
    CustomerProfile, BehaviorEvent, SegmentDefinition,
    ModelTrainingLog, PurchasePrediction,
)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'


class CustomerProfileSummarySerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'customer_id', 'customer_email', 'customer_name',
            'recency_days', 'frequency', 'monetary',
            'avg_order_value', 'segment_id', 'segment_name',
            'churn_risk', 'predicted_clv', 'last_computed',
        ]


class BehaviorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorEvent
        fields = '__all__'


class SegmentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentDefinition
        fields = '__all__'


class ModelTrainingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelTrainingLog
        fields = '__all__'


class PurchasePredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasePrediction
        fields = '__all__'


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard overview statistics."""
    total_customers = serializers.IntegerField()
    total_events = serializers.IntegerField()
    avg_churn_risk = serializers.FloatField()
    avg_clv = serializers.FloatField()
    total_predicted_revenue = serializers.FloatField()
    segments = SegmentDefinitionSerializer(many=True)
    churn_distribution = serializers.DictField()
    rfm_summary = serializers.DictField()
    recent_training = ModelTrainingLogSerializer(allow_null=True)
