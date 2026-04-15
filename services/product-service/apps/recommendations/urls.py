from django.urls import path
from . import views

urlpatterns = [
    path('track/', views.TrackProductView.as_view(), name='track-view'),
    path('', views.GetRecommendations.as_view(), name='get-recommendations'),
    path('trending/', views.TrendingCategories.as_view(), name='trending-categories'),
]
