from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image_url', 'product_count', 'created_at']

    def get_product_count(self, obj):
        return obj.products.count()


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_price', 'image_url',
                  'category', 'category_name', 'stock', 'is_in_stock',
                  'discount_percent', 'rating', 'num_reviews', 'is_active']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'compare_price',
            'category', 'category_name', 'image_url', 'stock',
            'is_active', 'rating', 'num_reviews', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'category_name', 'created_at', 'updated_at']
        extra_kwargs = {'slug': {'required': False, 'allow_blank': True}}

    def validate(self, attrs):
        price = attrs.get('price', getattr(self.instance, 'price', None))
        compare_price = attrs.get('compare_price', getattr(self.instance, 'compare_price', None))

        if compare_price is not None and price is not None and compare_price < price:
            raise serializers.ValidationError({'compare_price': 'Compare price must be greater than or equal to price.'})
        return attrs

    def _generate_unique_slug(self, name):
        base_slug = slugify(name) or 'product'
        slug = base_slug
        idx = 2

        while True:
            queryset = Product.objects.filter(slug=slug)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if not queryset.exists():
                return slug
            slug = f'{base_slug}-{idx}'
            idx += 1

    def create(self, validated_data):
        if not validated_data.get('slug'):
            validated_data['slug'] = self._generate_unique_slug(validated_data.get('name', 'product'))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'slug' in validated_data and not validated_data['slug']:
            validated_data['slug'] = self._generate_unique_slug(validated_data.get('name', instance.name))
        return super().update(instance, validated_data)
