from django.contrib import admin
from .models import (
    CustomerProfile, BehaviorEvent, SegmentDefinition,
    ModelTrainingLog, PurchasePrediction,
)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'segment_name', 'churn_risk',
                    'predicted_clv', 'frequency', 'monetary', 'last_computed']
    list_filter = ['segment_name']
    search_fields = ['customer_email', 'customer_name']


@admin.register(BehaviorEvent)
class BehaviorEventAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'event_type', 'product_name', 'amount', 'timestamp']
    list_filter = ['event_type']


@admin.register(SegmentDefinition)
class SegmentDefinitionAdmin(admin.ModelAdmin):
    list_display = ['segment_id', 'name', 'customer_count', 'avg_clv', 'avg_churn_risk']


@admin.register(ModelTrainingLog)
class ModelTrainingLogAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'version', 'final_loss', 'accuracy',
                    'num_samples', 'is_active', 'created_at']
    list_filter = ['model_name', 'is_active']


@admin.register(PurchasePrediction)
class PurchasePredictionAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'product_name', 'confidence', 'predicted_at']
