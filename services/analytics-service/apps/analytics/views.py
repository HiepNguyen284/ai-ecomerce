"""
API Views for Customer Behavior Analytics Dashboard.

Provides endpoints for:
- Dashboard overview statistics
- Customer profiles (list, detail)
- Segment analysis
- Chart data (segments, churn, RFM, trends, categories)
- Predictions
- Training logs
"""

import logging
from collections import Counter
from django.db.models import Avg, Sum, Count, Q, F, Max, Min
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    CustomerProfile, BehaviorEvent, SegmentDefinition,
    ModelTrainingLog, PurchasePrediction,
)
from .serializers import (
    CustomerProfileSerializer, CustomerProfileSummarySerializer,
    BehaviorEventSerializer, SegmentDefinitionSerializer,
    ModelTrainingLogSerializer,
)

logger = logging.getLogger(__name__)


class DashboardView(APIView):
    """Main dashboard with overview statistics."""

    def get(self, request):
        profiles = CustomerProfile.objects.all()
        total_customers = profiles.count()

        if total_customers == 0:
            return Response({
                'total_customers': 0,
                'total_events': BehaviorEvent.objects.count(),
                'avg_churn_risk': 0,
                'avg_clv': 0,
                'total_predicted_revenue': 0,
                'segments': [],
                'churn_distribution': {'low': 0, 'medium': 0, 'high': 0},
                'rfm_summary': {},
                'recent_training': None,
                'models_trained': False,
            })

        agg = profiles.aggregate(
            avg_churn=Avg('churn_risk'),
            avg_clv=Avg('predicted_clv'),
            total_revenue=Sum('predicted_clv'),
            avg_monetary=Avg('monetary'),
            avg_frequency=Avg('frequency'),
            avg_recency=Avg('recency_days'),
            max_clv=Max('predicted_clv'),
            min_clv=Min('predicted_clv'),
        )

        # Churn distribution
        churn_low = profiles.filter(churn_risk__lt=0.3).count()
        churn_med = profiles.filter(churn_risk__gte=0.3, churn_risk__lt=0.7).count()
        churn_high = profiles.filter(churn_risk__gte=0.7).count()

        # Segments
        segments = SegmentDefinition.objects.all()

        # Recent training
        recent_training = ModelTrainingLog.objects.filter(
            is_active=True).first()

        # Top spenders
        top_spenders = profiles.order_by('-monetary')[:5]

        # At-risk customers
        at_risk = profiles.filter(churn_risk__gte=0.7).order_by('-churn_risk')[:5]

        return Response({
            'total_customers': total_customers,
            'total_events': BehaviorEvent.objects.count(),
            'avg_churn_risk': round(agg['avg_churn'] or 0, 4),
            'avg_clv': round(float(agg['avg_clv'] or 0), 2),
            'total_predicted_revenue': round(
                float(agg['total_revenue'] or 0), 2),
            'avg_monetary': round(float(agg['avg_monetary'] or 0), 2),
            'avg_frequency': round(float(agg['avg_frequency'] or 0), 2),
            'avg_recency': round(float(agg['avg_recency'] or 0), 1),
            'max_clv': round(float(agg['max_clv'] or 0), 2),
            'segments': SegmentDefinitionSerializer(segments, many=True).data,
            'churn_distribution': {
                'low': churn_low,
                'medium': churn_med,
                'high': churn_high,
            },
            'rfm_summary': {
                'avg_recency': round(float(agg['avg_recency'] or 0), 1),
                'avg_frequency': round(float(agg['avg_frequency'] or 0), 2),
                'avg_monetary': round(float(agg['avg_monetary'] or 0), 2),
            },
            'top_spenders': CustomerProfileSummarySerializer(
                top_spenders, many=True).data,
            'at_risk_customers': CustomerProfileSummarySerializer(
                at_risk, many=True).data,
            'recent_training': ModelTrainingLogSerializer(
                recent_training).data if recent_training else None,
            'models_trained': recent_training is not None,
        })


class CustomerProfileListView(APIView):
    """List all customer profiles with optional filtering."""

    def get(self, request):
        profiles = CustomerProfile.objects.all()

        # Filters
        segment = request.query_params.get('segment')
        if segment:
            profiles = profiles.filter(segment_id=segment)

        churn_risk = request.query_params.get('churn_risk')
        if churn_risk == 'high':
            profiles = profiles.filter(churn_risk__gte=0.7)
        elif churn_risk == 'medium':
            profiles = profiles.filter(churn_risk__gte=0.3, churn_risk__lt=0.7)
        elif churn_risk == 'low':
            profiles = profiles.filter(churn_risk__lt=0.3)

        # Sorting
        sort_by = request.query_params.get('sort', '-monetary')
        allowed_sorts = [
            'monetary', '-monetary', 'churn_risk', '-churn_risk',
            'predicted_clv', '-predicted_clv', 'frequency', '-frequency',
            'recency_days', '-recency_days',
        ]
        if sort_by in allowed_sorts:
            profiles = profiles.order_by(sort_by)

        # Search
        search = request.query_params.get('search')
        if search:
            profiles = profiles.filter(
                Q(customer_email__icontains=search) |
                Q(customer_name__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = profiles.count()
        data = CustomerProfileSummarySerializer(
            profiles[start:end], many=True).data

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': data,
        })


class CustomerProfileDetailView(APIView):
    """Get detailed profile for a specific customer."""

    def get(self, request, customer_id):
        try:
            profile = CustomerProfile.objects.get(customer_id=customer_id)
        except CustomerProfile.DoesNotExist:
            return Response({'error': 'Customer profile not found.'},
                          status=status.HTTP_404_NOT_FOUND)

        data = CustomerProfileSerializer(profile).data

        # Add recent events
        events = BehaviorEvent.objects.filter(
            customer_id=customer_id
        ).order_by('-timestamp')[:50]
        data['recent_events'] = BehaviorEventSerializer(events, many=True).data

        # Add predictions
        predictions = PurchasePrediction.objects.filter(
            customer_id=customer_id
        ).order_by('-confidence')[:10]
        data['purchase_predictions'] = [{
            'product_name': p.product_name,
            'category_name': p.category_name,
            'confidence': p.confidence,
        } for p in predictions]

        # Add segment info
        try:
            segment = SegmentDefinition.objects.get(
                segment_id=profile.segment_id)
            data['segment_info'] = SegmentDefinitionSerializer(segment).data
        except SegmentDefinition.DoesNotExist:
            data['segment_info'] = None

        return Response(data)


class CustomerEventsView(APIView):
    """Get behavior events for a specific customer."""

    def get(self, request, customer_id):
        events = BehaviorEvent.objects.filter(
            customer_id=customer_id
        ).order_by('-timestamp')

        event_type = request.query_params.get('type')
        if event_type:
            events = events.filter(event_type=event_type)

        page_size = int(request.query_params.get('page_size', 50))
        data = BehaviorEventSerializer(events[:page_size], many=True).data
        return Response(data)


class SegmentListView(APIView):
    """List all customer segments with their statistics."""

    def get(self, request):
        segments = SegmentDefinition.objects.all()
        data = SegmentDefinitionSerializer(segments, many=True).data

        # Enrich with extra stats per segment
        for seg_data in data:
            seg_id = seg_data['segment_id']
            profiles = CustomerProfile.objects.filter(segment_id=seg_id)
            seg_data['top_categories'] = self._get_top_categories(profiles)

        return Response(data)

    def _get_top_categories(self, profiles, limit=5):
        """Get most popular categories for a segment."""
        category_counts = Counter()
        for profile in profiles[:100]:  # Sample for performance
            for cat, weight in profile.category_distribution.items():
                category_counts[cat] += weight
        return [{'name': cat, 'weight': round(w, 3)}
                for cat, w in category_counts.most_common(limit)]


class SegmentCustomersView(APIView):
    """List customers in a specific segment."""

    def get(self, request, segment_id):
        profiles = CustomerProfile.objects.filter(
            segment_id=segment_id
        ).order_by('-monetary')

        page_size = int(request.query_params.get('page_size', 20))
        data = CustomerProfileSummarySerializer(
            profiles[:page_size], many=True).data

        try:
            segment = SegmentDefinition.objects.get(segment_id=segment_id)
            segment_info = SegmentDefinitionSerializer(segment).data
        except SegmentDefinition.DoesNotExist:
            segment_info = None

        return Response({
            'segment': segment_info,
            'customers': data,
            'total': profiles.count(),
        })


class CustomerPredictionView(APIView):
    """Get ML predictions for a specific customer."""

    def get(self, request, customer_id):
        try:
            profile = CustomerProfile.objects.get(customer_id=customer_id)
        except CustomerProfile.DoesNotExist:
            return Response({'error': 'Customer not found.'},
                          status=status.HTTP_404_NOT_FOUND)

        return Response({
            'customer_id': str(customer_id),
            'segment': {
                'id': profile.segment_id,
                'name': profile.segment_name,
            },
            'churn_risk': profile.churn_risk,
            'churn_label': (
                'Cao' if profile.churn_risk > 0.7 else
                'Trung bình' if profile.churn_risk > 0.3 else 'Thấp'
            ),
            'predicted_clv': float(profile.predicted_clv),
            'top_categories': profile.top_categories,
            'embedding': profile.embedding[:8] if profile.embedding else [],
        })


class SegmentChartView(APIView):
    """Segment distribution chart data."""

    def get(self, request):
        segments = SegmentDefinition.objects.all()
        data = []
        for seg in segments:
            data.append({
                'name': seg.name_vi or seg.name,
                'value': seg.customer_count,
                'color': seg.color,
                'avg_clv': float(seg.avg_clv),
                'avg_monetary': float(seg.avg_monetary),
            })
        return Response(data)


class ChurnDistributionView(APIView):
    """Churn risk distribution chart data."""

    def get(self, request):
        profiles = CustomerProfile.objects.all()

        # Histogram bins
        bins = [
            (0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4),
            (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8),
            (0.8, 0.9), (0.9, 1.01),
        ]

        histogram = []
        for low, high in bins:
            count = profiles.filter(
                churn_risk__gte=low, churn_risk__lt=high).count()
            histogram.append({
                'range': f'{low:.0%}-{high:.0%}',
                'count': count,
                'low': low,
                'high': high,
            })

        # By segment
        by_segment = []
        for seg in SegmentDefinition.objects.all():
            seg_profiles = profiles.filter(segment_id=seg.segment_id)
            avg_churn = seg_profiles.aggregate(
                avg=Avg('churn_risk'))['avg'] or 0
            by_segment.append({
                'segment': seg.name_vi or seg.name,
                'avg_churn': round(avg_churn, 4),
                'color': seg.color,
                'count': seg_profiles.count(),
            })

        return Response({
            'histogram': histogram,
            'by_segment': by_segment,
        })


class RFMAnalysisView(APIView):
    """RFM analysis chart data."""

    def get(self, request):
        profiles = CustomerProfile.objects.all()

        if not profiles.exists():
            return Response({'scatter': [], 'distribution': {}})

        # Scatter plot data (R vs F, sized by M)
        scatter = []
        for p in profiles[:500]:  # Limit for performance
            scatter.append({
                'recency': p.recency_days,
                'frequency': p.frequency,
                'monetary': float(p.monetary),
                'segment': p.segment_name,
                'churn_risk': p.churn_risk,
                'customer_id': str(p.customer_id),
            })

        # RFM score distributions
        r_dist = list(profiles.values_list('recency_days', flat=True))
        f_dist = list(profiles.values_list('frequency', flat=True))
        m_dist = [float(v) for v in profiles.values_list('monetary', flat=True)]

        return Response({
            'scatter': scatter,
            'distribution': {
                'recency': {
                    'mean': round(sum(r_dist) / len(r_dist), 1) if r_dist else 0,
                    'median': sorted(r_dist)[len(r_dist) // 2] if r_dist else 0,
                    'max': max(r_dist) if r_dist else 0,
                },
                'frequency': {
                    'mean': round(sum(f_dist) / len(f_dist), 1) if f_dist else 0,
                    'median': sorted(f_dist)[len(f_dist) // 2] if f_dist else 0,
                    'max': max(f_dist) if f_dist else 0,
                },
                'monetary': {
                    'mean': round(sum(m_dist) / len(m_dist), 2) if m_dist else 0,
                    'median': round(sorted(m_dist)[len(m_dist) // 2], 2) if m_dist else 0,
                    'max': round(max(m_dist), 2) if m_dist else 0,
                },
            },
        })


class TrendAnalysisView(APIView):
    """Trend analysis over time."""

    def get(self, request):
        # Event counts by day (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

        daily_events = (
            BehaviorEvent.objects
            .filter(timestamp__gte=thirty_days_ago)
            .annotate(date=TruncDate('timestamp'))
            .values('date', 'event_type')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # Monthly revenue trend
        monthly_revenue = (
            BehaviorEvent.objects
            .filter(event_type='purchase')
            .annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(
                total_revenue=Sum('amount'),
                order_count=Count('id'),
            )
            .order_by('month')
        )

        return Response({
            'daily_events': list(daily_events),
            'monthly_revenue': [
                {
                    'month': str(r['month']),
                    'revenue': float(r['total_revenue'] or 0),
                    'orders': r['order_count'],
                }
                for r in monthly_revenue
            ],
        })


class CategoryInsightsView(APIView):
    """Category-level insights from behavior data."""

    def get(self, request):
        # Purchase counts by category
        category_stats = (
            BehaviorEvent.objects
            .filter(event_type='purchase')
            .values('category_name')
            .annotate(
                purchase_count=Count('id'),
                total_revenue=Sum('amount'),
                unique_customers=Count('customer_id', distinct=True),
                avg_amount=Avg('amount'),
            )
            .order_by('-total_revenue')
        )

        data = []
        for cat in category_stats:
            if not cat['category_name']:
                continue
            data.append({
                'category': cat['category_name'],
                'purchases': cat['purchase_count'],
                'revenue': float(cat['total_revenue'] or 0),
                'customers': cat['unique_customers'],
                'avg_amount': float(cat['avg_amount'] or 0),
            })

        return Response(data)


class TrainingLogListView(APIView):
    """List model training history."""

    def get(self, request):
        logs = ModelTrainingLog.objects.all()[:20]
        return Response(ModelTrainingLogSerializer(logs, many=True).data)


class HealthCheckView(APIView):
    """Health check endpoint."""

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'analytics-service',
        })
