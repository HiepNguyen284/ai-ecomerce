import requests
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, UpdateCartItemSerializer


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
        if resp.status_code == 200:
            data = resp.json()
            if data.get('valid'):
                return data['user_id']
    except requests.RequestException:
        pass
    return None


def get_product_info(product_id):
    """Fetch product info from product-service."""
    try:
        resp = requests.get(
            f'{settings.PRODUCT_SERVICE_URL}/products/by-id/{product_id}/',
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


class CartView(APIView):
    """Get or create the user's cart."""

    def get(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        cart, _ = Cart.objects.get_or_create(user_id=user_id)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    """Add item to cart."""

    def post(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = str(serializer.validated_data['product_id'])
        quantity = serializer.validated_data['quantity']

        # Fetch product info
        product = get_product_info(product_id)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart, _ = Cart.objects.get_or_create(user_id=user_id)

        # Check if item already exists in cart
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                product_name=product['name'],
                product_price=product['price'],
                product_image_url=product.get('image_url', ''),
                quantity=quantity,
            )

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    """Update quantity of a cart item."""

    def put(self, request, item_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user_id=user_id)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.quantity = serializer.validated_data['quantity']
            cart_item.save()
            return Response(CartSerializer(cart).data)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, item_id):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            cart = Cart.objects.get(user_id=user_id)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response(CartSerializer(cart).data)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)


class ClearCartView(APIView):
    """Clear all items from cart."""

    def delete(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            cart = Cart.objects.get(user_id=user_id)
            cart.items.all().delete()
            return Response(CartSerializer(cart).data)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)


class CartItemsForOrderView(APIView):
    """Internal endpoint: Return cart items for order creation."""

    def get(self, request, user_id):
        try:
            cart = Cart.objects.get(user_id=user_id)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'cart-service'})
