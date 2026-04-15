from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('suggestions/', views.SuggestionsView.as_view(), name='suggestions'),
    path('history/<str:session_id>/', views.ConversationHistoryView.as_view(), name='conversation-history'),
    path('conversation/<uuid:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
