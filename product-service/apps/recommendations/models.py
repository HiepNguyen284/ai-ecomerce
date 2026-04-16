import uuid
from django.db import models
from apps.products.models import Product, Category


class ProductView(models.Model):
    """Tracks individual product view events for behavior analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True,
                                  help_text='Anonymous session identifier')
    user_id = models.UUIDField(null=True, blank=True, db_index=True,
                               help_text='Authenticated user ID (from user-service)')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='view_events')
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='view_events')
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'product_views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['session_id', 'viewed_at']),
            models.Index(fields=['user_id', 'viewed_at']),
            models.Index(fields=['session_id', 'category']),
        ]

    def __str__(self):
        return f"View: {self.product.name} by {self.session_id}"


class CategoryPreference(models.Model):
    """Aggregated category preference scores per user/session.

    Updated periodically from ProductView events.
    The score is computed by the deep learning model and represents
    the user's affinity for each category.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='preferences')
    view_count = models.PositiveIntegerField(default=0,
                                             help_text='Raw number of views in this category')
    score = models.FloatField(default=0.0,
                              help_text='Deep learning model prediction score (0-1)')
    last_viewed = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'category_preferences'
        ordering = ['-score']
        unique_together = [['session_id', 'category']]
        indexes = [
            models.Index(fields=['session_id', '-score']),
            models.Index(fields=['user_id', '-score']),
        ]

    def __str__(self):
        return f"{self.session_id} -> {self.category.name}: {self.score:.2f}"
