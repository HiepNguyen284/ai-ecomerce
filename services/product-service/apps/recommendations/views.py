import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.products.models import Product, Category
from apps.products.serializers import ProductListSerializer
from .models import ProductView, CategoryPreference
from .serializers import (
    TrackViewSerializer,
    CategoryPreferenceSerializer,
)
from .engine import recommendation_engine

logger = logging.getLogger(__name__)


def _get_user_id_from_request(request):
    """Extract user_id from Authorization header via user-service validation."""
    import requests as http_requests
    from django.conf import settings

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        resp = http_requests.post(
            f'{settings.USER_SERVICE_URL}/users/validate-token/',
            json={'token': token},
            timeout=5,
        )
        if resp.status_code == 200 and resp.json().get('valid'):
            return resp.json().get('user_id')
    except http_requests.RequestException:
        pass
    return None


class TrackProductView(APIView):
    """Track a product view event for recommendation analysis.

    POST /products/recommendations/track/
    Body: { "product_id": "uuid", "session_id": "string" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TrackViewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        session_id = serializer.validated_data['session_id']
        user_id = _get_user_id_from_request(request)

        try:
            product = Product.objects.select_related('category').get(
                id=product_id, is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Throttle: don't record the same product view within 30 seconds
        recent_threshold = timezone.now() - timedelta(seconds=30)
        already_tracked = ProductView.objects.filter(
            session_id=session_id,
            product=product,
            viewed_at__gte=recent_threshold,
        ).exists()

        if not already_tracked:
            # Create view event
            ProductView.objects.create(
                session_id=session_id,
                user_id=user_id,
                product=product,
                category=product.category,
            )

            # Update aggregated preference
            pref, created = CategoryPreference.objects.get_or_create(
                session_id=session_id,
                category=product.category,
                defaults={'user_id': user_id, 'view_count': 0, 'score': 0.0},
            )
            pref.view_count += 1
            if user_id:
                pref.user_id = user_id
            pref.save()

            # Update deep learning model scores for this user
            try:
                preferences = CategoryPreference.objects.filter(
                    session_id=session_id
                ).select_related('category')
                categories = list(Category.objects.all())

                if preferences.exists() and categories:
                    loss = recommendation_engine.update_model(
                        preferences, categories
                    )
                    # Update scores in DB
                    scores = recommendation_engine.model.predict(
                        recommendation_engine.process_views(
                            preferences, categories
                        ),
                        len(categories),
                    )
                    for p in preferences:
                        cat_id = str(p.category_id)
                        if cat_id in recommendation_engine.category_index_map:
                            idx = recommendation_engine.category_index_map[cat_id]
                            p.score = float(scores[idx])
                            p.save(update_fields=['score', 'updated_at'])
            except Exception as e:
                logger.warning(f"Failed to update DL model: {e}")

        return Response({
            'status': 'tracked',
            'product': product.name,
            'category': product.category.name,
        })


class GetRecommendations(APIView):
    """Get personalized product recommendations.

    GET /products/recommendations/?session_id=xxx

    Returns recommended products based on the user's browsing history.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_id = request.query_params.get('session_id', '')
        if not session_id:
            # Return popular products if no session
            products = Product.objects.filter(is_active=True).order_by(
                '-rating', '-num_reviews'
            )[:20]
            return Response({
                'recommended_products': ProductListSerializer(
                    products, many=True
                ).data,
                'category_preferences': [],
                'analysis': {
                    'type': 'popular',
                    'message': 'Showing popular products (no browsing history)',
                },
            })

        user_id = _get_user_id_from_request(request)

        # Get user preferences
        preferences = CategoryPreference.objects.filter(
            session_id=session_id
        ).select_related('category').order_by('-score')

        # If user is authenticated, also merge any preferences from user_id
        if user_id:
            user_prefs = CategoryPreference.objects.filter(
                user_id=user_id
            ).exclude(session_id=session_id).select_related('category')
            # Merge: use union of both
            pref_ids = set(preferences.values_list('id', flat=True))
            pref_ids.update(user_prefs.values_list('id', flat=True))
            preferences = CategoryPreference.objects.filter(
                id__in=pref_ids
            ).select_related('category').order_by('-score')

        categories = Category.objects.all()
        all_products = Product.objects.filter(
            is_active=True
        ).select_related('category')

        # Get recommendations from DL engine
        recommended = recommendation_engine.get_recommendations(
            preferences, categories, all_products, max_products=20
        )

        # Build analysis info
        total_views = (
            preferences.aggregate(total=Sum('view_count'))['total'] or 0
        )
        top_cats = list(
            preferences[:5].values_list('category__name', flat=True)
        )

        analysis = {
            'type': 'personalized' if preferences.exists() else 'popular',
            'total_views': total_views,
            'top_categories': top_cats,
            'model_trained': (
                recommendation_engine.model.trained
                if recommendation_engine.model
                else False
            ),
            'message': (
                f'Recommendations based on {total_views} product views '
                f'across {preferences.count()} categories'
                if preferences.exists()
                else 'Showing popular products'
            ),
        }

        return Response({
            'recommended_products': ProductListSerializer(
                recommended, many=True
            ).data,
            'category_preferences': CategoryPreferenceSerializer(
                preferences[:10], many=True
            ).data,
            'analysis': analysis,
        })


class TrendingCategories(APIView):
    """Get trending categories based on overall user behavior.

    GET /products/recommendations/trending/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Find categories with most views in last 7 days
        since = timezone.now() - timedelta(days=7)

        trending = (
            ProductView.objects.filter(viewed_at__gte=since)
            .values('category__id', 'category__name')
            .annotate(total_views=Count('id'))
            .order_by('-total_views')[:10]
        )

        # For each trending category, get top products
        results = []
        for t in trending:
            products = Product.objects.filter(
                category_id=t['category__id'], is_active=True
            ).order_by('-rating', '-num_reviews')[:5]

            results.append({
                'category_id': str(t['category__id']),
                'category_name': t['category__name'],
                'total_views': t['total_views'],
                'top_products': ProductListSerializer(
                    products, many=True
                ).data,
            })

        return Response({'trending': results})
