from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/recommendations/', include('apps.recommendations.urls')),
    path('products/', include('apps.products.urls')),
]
