from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('items/<uuid:item_id>/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('clear/', views.ClearCartView.as_view(), name='clear-cart'),
    path('internal/<uuid:user_id>/', views.CartItemsForOrderView.as_view(), name='cart-for-order'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
