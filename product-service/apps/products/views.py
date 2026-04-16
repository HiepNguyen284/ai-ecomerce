import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductAdminSerializer,
)


def get_user_from_token(request):
    """Validate JWT token via user-service and return user context."""
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
            return resp.json()
    except requests.RequestException:
        pass
    return None


def ensure_admin_user(request):
    user_data = get_user_from_token(request)
    if not user_data:
        return None, Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not user_data.get('is_staff'):
        return None, Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
    return user_data, None


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'rating', 'name']
    ordering = ['-created_at']


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class ProductByIdView(generics.RetrieveAPIView):
    """Retrieve product by UUID — used internally by other services."""
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'


class ProductStockCheckView(APIView):
    """Internal endpoint: check stock availability for a list of product IDs."""
    permission_classes = [AllowAny]

    def post(self, request):
        items = request.data.get('items', [])
        result = []
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'])
                result.append({
                    'product_id': str(product.id),
                    'name': product.name,
                    'price': str(product.price),
                    'stock': product.stock,
                    'requested': item.get('quantity', 1),
                    'available': product.stock >= item.get('quantity', 1),
                })
            except Product.DoesNotExist:
                result.append({
                    'product_id': item['product_id'],
                    'available': False,
                    'error': 'Product not found',
                })
        return Response({'items': result})


class AdminProductListCreateView(APIView):
    """Admin: list all products and create new product."""
    permission_classes = [AllowAny]

    def get(self, request):
        _, error = ensure_admin_user(request)
        if error:
            return error

        products = Product.objects.select_related('category').all().order_by('-created_at')
        serializer = ProductAdminSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        _, error = ensure_admin_user(request)
        if error:
            return error

        serializer = ProductAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminProductDetailView(APIView):
    """Admin: retrieve, update and delete a product by ID."""
    permission_classes = [AllowAny]

    def _get_product(self, pk):
        try:
            return Product.objects.select_related('category').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        _, error = ensure_admin_user(request)
        if error:
            return error

        product = self._get_product(pk)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductAdminSerializer(product).data)

    def patch(self, request, pk):
        _, error = ensure_admin_user(request)
        if error:
            return error

        product = self._get_product(pk)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductAdminSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        _, error = ensure_admin_user(request)
        if error:
            return error

        product = self._get_product(pk)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductAdminSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        _, error = ensure_admin_user(request)
        if error:
            return error

        product = self._get_product(pk)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RelatedProductsView(APIView):
    """Return related products from the same category."""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.select_related('category').get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        related = Product.objects.filter(
            category=product.category,
            is_active=True,
        ).exclude(id=product.id).order_by('?')[:8]

        serializer = ProductListSerializer(related, many=True)
        return Response(serializer.data)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'product-service'})
