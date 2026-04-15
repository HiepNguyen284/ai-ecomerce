from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.CreateOrderView.as_view(), name='create-order'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:order_id>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('<uuid:order_id>/status/', views.UpdateOrderStatusView.as_view(), name='update-order-status'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
