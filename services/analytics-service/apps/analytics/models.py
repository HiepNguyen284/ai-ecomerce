import uuid
from django.db import models


class CustomerProfile(models.Model):
    """
    Stores computed customer behavior profiles and ML predictions.
    Updated periodically by the deep learning pipeline.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(unique=True, db_index=True)
    customer_email = models.EmailField(blank=True)
    customer_name = models.CharField(max_length=255, blank=True)

    # === RFM Features ===
    recency_days = models.IntegerField(default=0, help_text='Days since last purchase')
    frequency = models.IntegerField(default=0, help_text='Total number of orders')
    monetary = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                   help_text='Total amount spent')

    # === Behavioral Features ===
    avg_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_items_purchased = models.IntegerField(default=0)
    unique_products_bought = models.IntegerField(default=0)
    unique_categories_bought = models.IntegerField(default=0)
    avg_items_per_order = models.FloatField(default=0)
    cancelled_order_ratio = models.FloatField(default=0)
    days_as_customer = models.IntegerField(default=0, help_text='Days since registration')
    order_frequency_monthly = models.FloatField(default=0, help_text='Avg orders per month')

    # === Time Pattern Features ===
    preferred_hour = models.IntegerField(default=0, help_text='Most common purchase hour')
    preferred_day_of_week = models.IntegerField(default=0, help_text='Most common day (0=Mon)')
    weekend_purchase_ratio = models.FloatField(default=0)

    # === Category Preferences (JSON) ===
    category_distribution = models.JSONField(default=dict,
                                              help_text='Category purchase distribution')
    top_categories = models.JSONField(default=list,
                                      help_text='Top 5 preferred categories')

    # === ML Predictions ===
    segment_id = models.IntegerField(default=0, help_text='Cluster segment ID')
    segment_name = models.CharField(max_length=100, blank=True, help_text='Human-readable segment')
    churn_risk = models.FloatField(default=0, help_text='Churn probability 0-1')
    predicted_clv = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                        help_text='Predicted Customer Lifetime Value')

    # === Embedding Vector ===
    embedding = models.JSONField(default=list,
                                  help_text='Dense vector from autoencoder')

    # === Metadata ===
    last_computed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_profiles'
        ordering = ['-monetary']

    def __str__(self):
        return f'Profile: {self.customer_email} (Segment: {self.segment_name})'


class BehaviorEvent(models.Model):
    """
    Individual behavior events for each customer, used as training data.
    """
    class EventType(models.TextChoices):
        VIEW = 'view', 'Product View'
        ADD_TO_CART = 'add_to_cart', 'Add to Cart'
        REMOVE_FROM_CART = 'remove_from_cart', 'Remove from Cart'
        PURCHASE = 'purchase', 'Purchase'
        CANCEL = 'cancel', 'Order Cancelled'
        REVIEW = 'review', 'Product Review'
        SEARCH = 'search', 'Search'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    product_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    category_name = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'behavior_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['customer_id', 'event_type']),
            models.Index(fields=['customer_id', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.event_type} by {self.customer_id} at {self.timestamp}'


class SegmentDefinition(models.Model):
    """
    Customer segments discovered by the clustering model.
    """
    id = models.AutoField(primary_key=True)
    segment_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    name_vi = models.CharField(max_length=100, blank=True, help_text='Vietnamese name')
    description = models.TextField(blank=True)
    description_vi = models.TextField(blank=True, help_text='Vietnamese description')
    color = models.CharField(max_length=7, default='#6366f1')
    icon = models.CharField(max_length=50, default='users')
    customer_count = models.IntegerField(default=0)
    avg_clv = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_order_frequency = models.FloatField(default=0)
    avg_monetary = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_churn_risk = models.FloatField(default=0)
    centroid = models.JSONField(default=list, help_text='Cluster centroid vector')

    class Meta:
        db_table = 'segment_definitions'
        ordering = ['segment_id']

    def __str__(self):
        return f'Segment {self.segment_id}: {self.name}'


class ModelTrainingLog(models.Model):
    """
    Logs for deep learning model training runs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    epochs = models.IntegerField(default=0)
    final_loss = models.FloatField(default=0)
    accuracy = models.FloatField(null=True, blank=True)
    metrics = models.JSONField(default=dict)
    num_samples = models.IntegerField(default=0)
    training_duration_seconds = models.FloatField(default=0)
    model_path = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=False,
                                     help_text='Whether this version is currently serving')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'model_training_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.model_name} v{self.version} (loss={self.final_loss:.4f})'


class PurchasePrediction(models.Model):
    """
    Stores per-customer product purchase predictions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255, blank=True)
    category_name = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(default=0, help_text='Prediction confidence 0-1')
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_predictions'
        ordering = ['-confidence']
        unique_together = ['customer_id', 'product_id']

    def __str__(self):
        return f'Predict: {self.customer_id} → {self.product_name} ({self.confidence:.2%})'
