"""
Views for the AI Behavior Analysis Service.

Provides API endpoints for:
- Dataset info and CSV download
- User behavior queries and statistics
- Behavior analytics and insights
"""

import os
import csv
from datetime import datetime

from django.conf import settings
from django.db.models import Count, Min, Max, Q
from django.http import HttpResponse, FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserBehavior
from .serializers import (
    UserBehaviorSerializer,
    BehaviorStatsSerializer,
    UserSummarySerializer,
    DatasetInfoSerializer,
)
from .data_generator import generate_behavior_data, ACTIONS


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'ai-service',
        'version': '1.0.0',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def dataset_info(request):
    """
    Get metadata about the generated dataset.
    Shows total records, users, products, action distribution, etc.
    """
    total_records = UserBehavior.objects.count()

    if total_records == 0:
        return Response({
            'message': 'No data loaded. Run generate_behavior_data command first.',
        }, status=status.HTTP_404_NOT_FOUND)

    action_dist = dict(
        UserBehavior.objects.values_list('action')
        .annotate(count=Count('id'))
        .values_list('action', 'count')
    )

    date_range = UserBehavior.objects.aggregate(
        start=Min('timestamp'),
        end=Max('timestamp'),
    )

    data_dir = getattr(settings, 'DATA_DIR', os.path.join(settings.BASE_DIR, 'data'))
    csv_path = os.path.join(data_dir, 'data_user500.csv')

    data = {
        'total_records': total_records,
        'total_users': UserBehavior.objects.values('user_id').distinct().count(),
        'total_products': UserBehavior.objects.values('product_id').distinct().count(),
        'action_types': ACTIONS,
        'action_distribution': action_dist,
        'date_range': {
            'start': date_range['start'].isoformat() if date_range['start'] else None,
            'end': date_range['end'].isoformat() if date_range['end'] else None,
        },
        'csv_path': csv_path,
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def download_csv(request):
    """Download the data_user500.csv file."""
    data_dir = getattr(settings, 'DATA_DIR', os.path.join(settings.BASE_DIR, 'data'))
    csv_path = os.path.join(data_dir, 'data_user500.csv')

    if not os.path.exists(csv_path):
        return Response(
            {'error': 'CSV file not found. Run generate_behavior_data command first.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    response = FileResponse(
        open(csv_path, 'rb'),
        content_type='text/csv',
    )
    response['Content-Disposition'] = 'attachment; filename="data_user500.csv"'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def behavior_list(request):
    """
    List user behavior records with filtering.

    Query params:
    - user_id: filter by user
    - product_id: filter by product
    - action: filter by action type
    - limit: max results (default 100)
    - offset: pagination offset
    """
    queryset = UserBehavior.objects.all()

    # Apply filters
    user_id = request.query_params.get('user_id')
    product_id = request.query_params.get('product_id')
    action = request.query_params.get('action')

    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if product_id:
        queryset = queryset.filter(product_id=product_id)
    if action:
        queryset = queryset.filter(action=action)

    # Pagination
    limit = min(int(request.query_params.get('limit', 100)), 1000)
    offset = int(request.query_params.get('offset', 0))

    total = queryset.count()
    records = queryset[offset:offset + limit]

    serializer = UserBehaviorSerializer(records, many=True)

    return Response({
        'total': total,
        'limit': limit,
        'offset': offset,
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def action_stats(request):
    """
    Get aggregated statistics for all 8 action types.
    Returns count and percentage for each action.
    """
    total = UserBehavior.objects.count()

    if total == 0:
        return Response({'message': 'No data available.'}, status=status.HTTP_404_NOT_FOUND)

    stats = (
        UserBehavior.objects
        .values('action')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    result = []
    for item in stats:
        result.append({
            'action': item['action'],
            'count': item['count'],
            'percentage': round(item['count'] / total * 100, 2),
        })

    return Response({
        'total_records': total,
        'stats': result,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def user_summary(request, user_id):
    """
    Get behavior summary for a specific user.

    Returns total actions, unique products, action breakdown,
    and activity time range.
    """
    behaviors = UserBehavior.objects.filter(user_id=user_id)

    if not behaviors.exists():
        return Response(
            {'error': f'No data found for user {user_id}'},
            status=status.HTTP_404_NOT_FOUND,
        )

    action_breakdown = dict(
        behaviors.values_list('action')
        .annotate(count=Count('id'))
        .values_list('action', 'count')
    )

    time_range = behaviors.aggregate(
        first_activity=Min('timestamp'),
        last_activity=Max('timestamp'),
    )

    data = {
        'user_id': user_id,
        'total_actions': behaviors.count(),
        'unique_products': behaviors.values('product_id').distinct().count(),
        'actions_breakdown': action_breakdown,
        'first_activity': time_range['first_activity'],
        'last_activity': time_range['last_activity'],
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def top_products(request):
    """
    Get top products by interaction count.

    Query params:
    - action: filter by action type (e.g., 'purchase')
    - limit: max results (default 20)
    """
    action = request.query_params.get('action')
    limit = min(int(request.query_params.get('limit', 20)), 100)

    queryset = UserBehavior.objects.all()
    if action:
        queryset = queryset.filter(action=action)

    top = (
        queryset
        .values('product_id')
        .annotate(
            total_interactions=Count('id'),
            unique_users=Count('user_id', distinct=True),
        )
        .order_by('-total_interactions')[:limit]
    )

    return Response({
        'action_filter': action,
        'results': list(top),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def top_users(request):
    """
    Get most active users by interaction count.

    Query params:
    - action: filter by action type
    - limit: max results (default 20)
    """
    action = request.query_params.get('action')
    limit = min(int(request.query_params.get('limit', 20)), 100)

    queryset = UserBehavior.objects.all()
    if action:
        queryset = queryset.filter(action=action)

    top = (
        queryset
        .values('user_id')
        .annotate(
            total_interactions=Count('id'),
            unique_products=Count('product_id', distinct=True),
        )
        .order_by('-total_interactions')[:limit]
    )

    return Response({
        'action_filter': action,
        'results': list(top),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def regenerate_data(request):
    """
    Regenerate the data_user500.csv dataset and reload into database.
    WARNING: This will delete all existing behavior data.
    """
    data_dir = getattr(settings, 'DATA_DIR', os.path.join(settings.BASE_DIR, 'data'))
    output_path = os.path.join(data_dir, 'data_user500.csv')

    stats, records = generate_behavior_data(output_path)

    # Reload into database
    UserBehavior.objects.all().delete()

    batch_size = 5000
    behaviors = []
    for record in records:
        behaviors.append(UserBehavior(
            user_id=record['user_id'],
            product_id=record['product_id'],
            action=record['action'],
            timestamp=datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S'),
        ))
        if len(behaviors) >= batch_size:
            UserBehavior.objects.bulk_create(behaviors)
            behaviors = []
    if behaviors:
        UserBehavior.objects.bulk_create(behaviors)

    return Response({
        'message': 'Data regenerated successfully',
        'stats': stats,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def funnel_analysis(request):
    """
    Analyze the user behavior funnel.

    Shows how users progress through the 8 stages:
    view -> click -> search -> add_to_cart -> add_to_wishlist -> purchase -> review -> share

    Returns conversion rates between each stage.
    """
    funnel_stages = ['view', 'click', 'search', 'add_to_cart', 'add_to_wishlist', 'purchase', 'review', 'share']

    stage_data = []
    prev_users = None

    for stage_action in funnel_stages:
        users_at_stage = set(
            UserBehavior.objects
            .filter(action=stage_action)
            .values_list('user_id', flat=True)
            .distinct()
        )

        count = len(users_at_stage)

        if prev_users is not None:
            conversion = round(count / len(prev_users) * 100, 2) if prev_users else 0
        else:
            conversion = 100.0

        stage_data.append({
            'stage': stage_action,
            'unique_users': count,
            'conversion_rate': conversion,
        })

        prev_users = users_at_stage

    return Response({
        'funnel': stage_data,
        'total_users': UserBehavior.objects.values('user_id').distinct().count(),
    })


# ──────────────────────────────────────────────
# RAG Chat API
# ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """
    RAG Chat endpoint.
    POST /ai/chat/
    Body: {"message": "Gợi ý sản phẩm cho user1"}
    """
    from .ml.rag_engine import rag_chat

    message = request.data.get('message', '').strip()
    if not message:
        return Response(
            {'error': 'Message is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = rag_chat(message)

    return Response({
        'message': message,
        'answer': result['answer'],
        'intent': result['intent'],
        'user_ref': result.get('user_ref'),
    })



# ──────────────────────────────────────────────
# AI Recommendations API (KB Graph-based)
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def ai_recommend_products(request):
    """
    GET /ai/recommendations/products/?category=X&limit=8
    Returns popular products from KB Graph for search/browse pages.
    """
    import logging
    logger = logging.getLogger(__name__)

    category = request.query_params.get('category', '')
    limit = int(request.query_params.get('limit', '8'))

    try:
        from .ml.kb_graph import _get_neo4j_driver
        driver = _get_neo4j_driver()

        with driver.session() as session:
            if category:
                # Products in a specific category, ranked by popularity
                result = session.run("""
                    MATCH (u:User)-[:PURCHASED]->(p:Product)
                          -[:BELONGS_TO]->(c:Category)
                    WHERE c.name CONTAINS $category
                    WITH p, c, count(DISTINCT u) AS buyers
                    OPTIONAL MATCH (v:User)-[:VIEWED]->(p)
                    WITH p, c, buyers, count(DISTINCT v) AS viewers
                    RETURN p.uuid AS id, p.name AS name, p.slug AS slug,
                           p.price AS price, c.name AS category,
                           buyers, viewers,
                           buyers + viewers AS score
                    ORDER BY score DESC
                    LIMIT $limit
                """, category=category, limit=limit)
            else:
                # Top products overall, ranked by purchases + views
                result = session.run("""
                    MATCH (u:User)-[:PURCHASED]->(p:Product)
                          -[:BELONGS_TO]->(c:Category)
                    WITH p, c, count(DISTINCT u) AS buyers
                    OPTIONAL MATCH (v:User)-[:VIEWED]->(p)
                    WITH p, c, buyers, count(DISTINCT v) AS viewers
                    RETURN p.uuid AS id, p.name AS name, p.slug AS slug,
                           p.price AS price, c.name AS category,
                           buyers, viewers,
                           buyers + viewers AS score
                    ORDER BY score DESC
                    LIMIT $limit
                """, limit=limit)

            products = []
            for record in result:
                products.append({
                    'id': record['id'],
                    'name': record['name'],
                    'slug': record['slug'] or '',
                    'price': record['price'],
                    'category_name': record['category'],
                    'buyers': record['buyers'],
                    'viewers': record['viewers'],
                    'ai_score': record['score'],
                    'source': 'kb_graph',
                })

        driver.close()
        return Response({
            'recommendations': products,
            'source': 'neo4j_kb_graph',
            'category_filter': category or 'all',
        })

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return Response({
            'recommendations': [],
            'error': str(e),
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def ai_recommend_cart(request):
    """
    GET /ai/recommendations/cart/?product_ids=uuid1,uuid2&limit=6
    Returns 'You may also like' products based on what other users
    who bought the same items also purchased.
    """
    import logging
    logger = logging.getLogger(__name__)

    product_ids_raw = request.query_params.get('product_ids', '')
    product_ids = [pid.strip() for pid in product_ids_raw.split(',') if pid.strip()]
    limit = int(request.query_params.get('limit', '6'))

    try:
        from .ml.kb_graph import _get_neo4j_driver
        driver = _get_neo4j_driver()

        with driver.session() as session:
            if product_ids:
                # Collaborative: users who bought these also bought...
                result = session.run("""
                    MATCH (buyer:User)-[:PURCHASED]->(cart_p:Product)
                    WHERE cart_p.uuid IN $pids
                    WITH buyer
                    MATCH (buyer)-[:PURCHASED]->(rec:Product)
                          -[:BELONGS_TO]->(c:Category)
                    WHERE NOT rec.uuid IN $pids
                    WITH rec, c, count(DISTINCT buyer) AS co_buyers
                    RETURN rec.uuid AS id, rec.name AS name,
                           rec.slug AS slug, rec.price AS price,
                           c.name AS category, co_buyers
                    ORDER BY co_buyers DESC
                    LIMIT $limit
                """, pids=product_ids, limit=limit)
            else:
                # Fallback: top purchased products
                result = session.run("""
                    MATCH (u:User)-[:PURCHASED]->(p:Product)
                          -[:BELONGS_TO]->(c:Category)
                    WITH p, c, count(DISTINCT u) AS buyers
                    RETURN p.uuid AS id, p.name AS name,
                           p.slug AS slug, p.price AS price,
                           c.name AS category, buyers AS co_buyers
                    ORDER BY buyers DESC
                    LIMIT $limit
                """, limit=limit)

            products = []
            for record in result:
                products.append({
                    'id': record['id'],
                    'name': record['name'],
                    'slug': record['slug'] or '',
                    'price': record['price'],
                    'category_name': record['category'],
                    'co_buyers': record['co_buyers'],
                    'source': 'kb_graph',
                })

        driver.close()
        return Response({
            'recommendations': products,
            'source': 'neo4j_kb_graph',
            'based_on': product_ids or 'popular',
        })

    except Exception as e:
        logger.error(f"Cart recommendation error: {e}")
        return Response({
            'recommendations': [],
            'error': str(e),
        })
