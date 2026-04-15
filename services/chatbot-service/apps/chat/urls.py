from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('history/<str:session_id>/', views.ChatHistoryView.as_view(), name='chat-history'),
    path('clear/<str:session_id>/', views.ChatClearView.as_view(), name='chat-clear'),
    path('suggestions/', views.SuggestionsView.as_view(), name='suggestions'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
