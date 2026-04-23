import uuid
from django.db import models


class UserBehavior(models.Model):
    """
    Tracks individual user behavior events on the e-commerce platform.

    Each record represents a single action performed by a user on a product.
    The 8 action types cover the full customer journey funnel:
        view -> click -> search -> add_to_cart -> add_to_wishlist ->
        purchase -> review -> share

    user_id and product_id store real UUIDs from user-service and product-service.
    """

    ACTION_CHOICES = [
        ('view', 'View'),
        ('click', 'Click'),
        ('search', 'Search'),
        ('add_to_cart', 'Add to Cart'),
        ('add_to_wishlist', 'Add to Wishlist'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('share', 'Share'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(
        max_length=36,
        db_index=True,
        help_text='User UUID from user-service'
    )
    product_id = models.CharField(
        max_length=36,
        db_index=True,
        help_text='Product UUID from product-service'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text='Type of user behavior action'
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text='When the action occurred'
    )

    class Meta:
        db_table = 'user_behaviors'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'action']),
            models.Index(fields=['product_id', 'action']),
            models.Index(fields=['user_id', 'timestamp']),
        ]

    def __str__(self):
        return f"User {self.user_id[:8]}... -> {self.action} -> Product {self.product_id[:8]}..."
