from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'product_price',
                  'product_image_url', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user_id', 'status', 'status_display', 'total_amount',
                  'shipping_address', 'shipping_name', 'shipping_phone',
                  'note', 'payment_id', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'total_amount', 'payment_id',
                            'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    shipping_name = serializers.CharField(max_length=255)
    shipping_phone = serializers.CharField(max_length=20)
    note = serializers.CharField(required=False, default='')
