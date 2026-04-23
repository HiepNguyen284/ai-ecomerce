from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),

    # Dataset
    path('dataset/info/', views.dataset_info, name='dataset-info'),
    path('dataset/download/', views.download_csv, name='dataset-download'),
    path('dataset/regenerate/', views.regenerate_data, name='dataset-regenerate'),

    # Behavior data
    path('behaviors/', views.behavior_list, name='behavior-list'),
    path('behaviors/stats/', views.action_stats, name='behavior-stats'),
    path('behaviors/funnel/', views.funnel_analysis, name='behavior-funnel'),

    # User analysis
    path('users/<str:user_id>/summary/', views.user_summary, name='user-summary'),
    path('users/top/', views.top_users, name='top-users'),

    # Product analysis
    path('products/top/', views.top_products, name='top-products'),

    # RAG Chat
    path('chat/', views.chat, name='chat-api'),

    # AI Recommendations (KB Graph)
    path('recommendations/products/', views.ai_recommend_products, name='ai-recommend-products'),
    path('recommendations/cart/', views.ai_recommend_cart, name='ai-recommend-cart'),
]
