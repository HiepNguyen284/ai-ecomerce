import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Conversation, Message
from .serializers import (
    ChatRequestSerializer,
    ConversationSerializer,
)
from . import rag_engine

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    Main chat endpoint.
    Receives a user message, runs it through the RAG pipeline,
    and returns an AI-generated product consultation response.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data['session_id']
        conversation_id = serializer.validated_data.get('conversation_id')

        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, session_id=session_id)
            except Conversation.DoesNotExist:
                conversation = Conversation.objects.create(session_id=session_id)
        else:
            conversation = Conversation.objects.create(session_id=session_id)

        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        # Build conversation history for context
        history_messages = conversation.messages.order_by('created_at').values('role', 'content')
        conversation_history = list(history_messages)

        # Run RAG pipeline
        try:
            response_text, product_ids = rag_engine.ask(
                user_query=user_message,
                conversation_history=conversation_history,
            )
        except Exception as e:
            logger.error(f'RAG engine error: {e}')
            response_text = (
                'Xin lỗi, mình đang gặp sự cố kỹ thuật. '
                'Bạn vui lòng thử lại sau nhé! 🙏'
            )
            product_ids = []

        # Save assistant response
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_text,
            product_refs=product_ids,
        )

        # Build product data for frontend cards
        products_data = []
        if product_ids:
            try:
                products_data = rag_engine.get_products_by_ids(product_ids[:5])
            except Exception as e:
                logger.error(f'Error fetching product metadata: {e}')

        return Response({
            'conversation_id': str(conversation.id),
            'response': response_text,
            'product_refs': product_ids,
            'products': products_data,
        })


class ConversationHistoryView(APIView):
    """Retrieve conversation history by session_id."""
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        conversations = Conversation.objects.filter(
            session_id=session_id
        ).prefetch_related('messages').order_by('-updated_at')[:10]

        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ConversationDetailView(APIView):
    """Retrieve a specific conversation with all messages."""
    permission_classes = [AllowAny]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.prefetch_related(
                'messages'
            ).get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)


class SuggestionsView(APIView):
    """Return predefined suggestion chips for the chat UI."""
    permission_classes = [AllowAny]

    def get(self, request):
        suggestions = [
            'Tư vấn laptop để làm việc văn phòng',
            'Điện thoại chụp ảnh đẹp dưới 15 triệu',
            'Tai nghe chống ồn tốt nhất',
            'Đồng hồ thông minh cho thể thao',
            'Sản phẩm gaming đáng mua nhất',
            'Giày chạy bộ tốt cho người mới',
            'Đồ gia dụng thông minh nên mua',
            'Sách lập trình hay nhất',
        ]
        return Response({'suggestions': suggestions})


class HealthCheckView(APIView):
    """Service health check."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            product_count = rag_engine.get_indexed_product_count()
        except Exception:
            product_count = 0

        return Response({
            'status': 'healthy',
            'service': 'chatbot-service',
            'indexed_products': product_count,
        })
