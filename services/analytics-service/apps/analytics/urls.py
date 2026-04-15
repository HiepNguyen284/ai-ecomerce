from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Customer Profiles
    path('customers/', views.CustomerProfileListView.as_view(),
         name='customer-list'),
    path('customers/<uuid:customer_id>/', views.CustomerProfileDetailView.as_view(),
         name='customer-detail'),
    path('customers/<uuid:customer_id>/events/',
         views.CustomerEventsView.as_view(), name='customer-events'),

    # Segments
    path('segments/', views.SegmentListView.as_view(), name='segment-list'),
    path('segments/<int:segment_id>/customers/',
         views.SegmentCustomersView.as_view(), name='segment-customers'),

    # Predictions
    path('predictions/<uuid:customer_id>/',
         views.CustomerPredictionView.as_view(), name='customer-prediction'),

    # Charts data
    path('charts/segments/', views.SegmentChartView.as_view(),
         name='segment-chart'),
    path('charts/churn/', views.ChurnDistributionView.as_view(),
         name='churn-chart'),
    path('charts/rfm/', views.RFMAnalysisView.as_view(), name='rfm-chart'),
    path('charts/trends/', views.TrendAnalysisView.as_view(),
         name='trend-chart'),
    path('charts/categories/', views.CategoryInsightsView.as_view(),
         name='category-chart'),

    # Training
    path('training/logs/', views.TrainingLogListView.as_view(),
         name='training-logs'),

    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
