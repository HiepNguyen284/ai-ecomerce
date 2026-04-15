from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer


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


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'product-service'})
