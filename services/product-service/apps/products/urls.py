from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('admin/products/', views.AdminProductListCreateView.as_view(), name='admin-product-list-create'),
    path('admin/products/<uuid:pk>/', views.AdminProductDetailView.as_view(), name='admin-product-detail'),
    path('stock-check/', views.ProductStockCheckView.as_view(), name='stock-check'),
    path('by-id/<uuid:pk>/', views.ProductByIdView.as_view(), name='product-by-id'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
