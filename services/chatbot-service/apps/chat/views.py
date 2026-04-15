import uuid
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import ChatSession, ChatMessage
from .rag_engine import generate_response

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    Main chatbot endpoint.
    Receives a message and optional session_id, returns AI response with product suggestions.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id', '').strip()

        if not message:
            return Response(
                {'error': 'Vui lòng nhập tin nhắn.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(message) > 1000:
            return Response(
                {'error': 'Tin nhắn quá dài. Tối đa 1000 ký tự.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create chat session
        if session_id:
            session, _ = ChatSession.objects.get_or_create(session_key=session_id)
        else:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(session_key=session_id)

        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=message,
        )

        # Build conversation history from session
        history_messages = ChatMessage.objects.filter(
            session=session
        ).order_by('-created_at')[:10]

        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in reversed(list(history_messages))
        ]

        # Generate response using RAG engine
        try:
            result = generate_response(message, conversation_history)
        except Exception as exc:
            logger.exception('Error generating chatbot response: %s', exc)
            result = {
                'response': '😅 Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau.',
                'products': [],
            }

        # Save assistant response
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=result.get('response', ''),
            product_data=result.get('products', []),
        )

        # Update session timestamp
        session.save()

        return Response({
            'session_id': session.session_key,
            'response': result.get('response', ''),
            'products': result.get('products', []),
        })


class ChatHistoryView(APIView):
    """Retrieve chat history for a session."""
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_key=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = ChatMessage.objects.filter(session=session).order_by('created_at')

        return Response({
            'session_id': session.session_key,
            'messages': [
                {
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'products': msg.product_data,
                    'created_at': msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        })


class ChatClearView(APIView):
    """Clear chat history for a session."""
    permission_classes = [AllowAny]

    def delete(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_key=session_id)
            session.messages.all().delete()
            return Response({'status': 'cleared'})
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )


class SuggestionsView(APIView):
    """Return predefined quick-reply suggestions."""
    permission_classes = [AllowAny]

    def get(self, request):
        suggestions = [
            '📱 Tư vấn điện thoại dưới 15 triệu',
            '💻 Laptop tốt nhất cho lập trình',
            '🎧 Tai nghe chống ồn nào tốt?',
            '👟 Giày thể thao giá rẻ',
            '⌚ So sánh Apple Watch và Galaxy Watch',
            '🎮 Máy chơi game cho gia đình',
        ]
        return Response({'suggestions': suggestions})


class HealthCheckView(APIView):
    """Health check endpoint."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'chatbot-service'})
