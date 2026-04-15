import requests
from decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer


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


class OrderListView(APIView):
    """List orders for authenticated user."""

    def get(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        orders = Order.objects.filter(user_id=user_id).prefetch_related('items')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class CreateOrderView(APIView):
    """Create order from user's cart."""

    def post(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Fetch cart items from cart-service
        try:
            cart_resp = requests.get(
                f'{settings.CART_SERVICE_URL}/cart/internal/{user_id}/',
                timeout=5,
            )
            if cart_resp.status_code != 200:
                return Response({'error': 'Could not fetch cart.'}, status=status.HTTP_400_BAD_REQUEST)
            cart_data = cart_resp.json()
        except requests.RequestException:
            return Response({'error': 'Cart service unavailable.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        cart_items = cart_data.get('items', [])
        if not cart_items:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        total = sum(Decimal(str(item['product_price'])) * item['quantity'] for item in cart_items)
        order = Order.objects.create(
            user_id=user_id,
            total_amount=total,
            shipping_address=serializer.validated_data['shipping_address'],
            shipping_name=serializer.validated_data['shipping_name'],
            shipping_phone=serializer.validated_data['shipping_phone'],
            note=serializer.validated_data.get('note', ''),
        )

        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                product_name=item['product_name'],
                product_price=item['product_price'],
                product_image_url=item.get('product_image_url', ''),
                quantity=item['quantity'],
            )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """Get order detail."""

    def get(self, request, order_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = Order.objects.prefetch_related('items').get(id=order_id, user_id=user_id)
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)


class CancelOrderView(APIView):
    """Cancel a pending order."""

    def post(self, request, order_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = Order.objects.get(id=order_id, user_id=user_id)
            if order.status != Order.Status.PENDING:
                return Response({'error': 'Only pending orders can be cancelled.'},
                                status=status.HTTP_400_BAD_REQUEST)
            order.status = Order.Status.CANCELLED
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)


class UpdateOrderStatusView(APIView):
    """Internal: Update order status (used by payment-service)."""

    def put(self, request, order_id):
        new_status = request.data.get('status')
        payment_id = request.data.get('payment_id')
        try:
            order = Order.objects.get(id=order_id)
            if new_status:
                order.status = new_status
            if payment_id:
                order.payment_id = payment_id
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'order-service'})
