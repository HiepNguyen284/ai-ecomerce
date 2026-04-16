import uuid
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer


def get_user_id_from_token(request):
    """Validate JWT token via user-service and return user_id."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        resp = requests.post(
            f'{settings.USER_SERVICE_URL}/users/validate-token/',
            json={'token': token},
            timeout=5,
        )
        if resp.status_code == 200 and resp.json().get('valid'):
            return resp.json()['user_id']
    except requests.RequestException:
        pass
    return None


class CreatePaymentView(APIView):
    """Create a payment for an order."""

    def post(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = str(serializer.validated_data['order_id'])
        method = serializer.validated_data['method']

        # Fetch order from order-service
        try:
            order_resp = requests.get(
                f'{settings.ORDER_SERVICE_URL}/orders/{order_id}/',
                headers={'Authorization': request.headers.get('Authorization', '')},
                timeout=5,
            )
            if order_resp.status_code != 200:
                return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
            order_data = order_resp.json()
        except requests.RequestException:
            return Response({'error': 'Order service unavailable.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Check if payment already exists
        if Payment.objects.filter(order_id=order_id, status__in=['pending', 'completed']).exists():
            return Response({'error': 'Payment already exists for this order.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create payment (simulate processing)
        transaction_id = f'TXN-{uuid.uuid4().hex[:12].upper()}'
        payment = Payment.objects.create(
            order_id=order_id,
            user_id=user_id,
            amount=order_data['total_amount'],
            method=method,
            status=Payment.Status.COMPLETED if method == 'cod' else Payment.Status.COMPLETED,
            transaction_id=transaction_id,
        )

        # Update order status via order-service
        try:
            requests.put(
                f'{settings.ORDER_SERVICE_URL}/orders/{order_id}/status/',
                json={'status': 'confirmed', 'payment_id': str(payment.id)},
                timeout=5,
            )
        except requests.RequestException:
            pass  # Non-critical: order status update can be retried

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentListView(APIView):
    """List payments for authenticated user."""

    def get(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        payments = Payment.objects.filter(user_id=user_id)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentDetailView(APIView):
    """Get payment detail."""

    def get(self, request, payment_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payment = Payment.objects.get(id=payment_id, user_id=user_id)
            return Response(PaymentSerializer(payment).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)


class PaymentByOrderView(APIView):
    """Get payment by order ID."""

    def get(self, request, order_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payment = Payment.objects.get(order_id=order_id, user_id=user_id)
            return Response(PaymentSerializer(payment).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'payment-service'})
