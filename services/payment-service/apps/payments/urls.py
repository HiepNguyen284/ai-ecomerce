from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('create/', views.CreatePaymentView.as_view(), name='create-payment'),
    path('order/<uuid:order_id>/', views.PaymentByOrderView.as_view(), name='payment-by-order'),
    path('<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
