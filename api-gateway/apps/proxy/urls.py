"""
API Gateway URL Configuration
==============================
Routes:
  /api/{service_name}/<path>  →  Proxied to the matching microservice
  /health                     →  Gateway health check
  /services                   →  List registered services
  /<path>                     →  Proxied to frontend (SPA catch-all, must be last)
"""
from django.urls import path, re_path
from . import views

urlpatterns = [
    # Gateway management endpoints
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('services/', views.ServiceRegistryView.as_view(), name='services'),

    # API proxy routes: /api/{service_name}/...
    re_path(
        r'^api/(?P<service_name>[a-z_-]+)/(?P<path>.*)$',
        views.ServiceProxyView.as_view(),
        name='service-proxy',
    ),

    # Frontend catch-all (must be last)
    re_path(
        r'^(?P<path>.*)$',
        views.FrontendProxyView.as_view(),
        name='frontend-proxy',
    ),
]
