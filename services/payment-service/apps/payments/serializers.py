from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'user_id', 'amount', 'method', 'method_display',
                  'status', 'status_display', 'transaction_id', 'note',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'status', 'transaction_id',
                            'created_at', 'updated_at']


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=Payment.Method.choices)
