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
from .knowledge_base import fetch_all_categories

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
        base_suggestions = [
            'Gợi ý sản phẩm đang giảm giá mạnh nhất',
            'Tư vấn sản phẩm phù hợp ngân sách dưới 3 triệu',
            'Sản phẩm nào được đánh giá cao và còn hàng?',
            'Cho mình top sản phẩm bán chạy hiện tại',
        ]

        category_suggestions = []
        categories = fetch_all_categories()
        category_names = []

        for item in categories:
            if isinstance(item, dict):
                raw_name = str(item.get('name') or item.get('slug') or '').strip()
            else:
                raw_name = str(item or '').strip()

            if not raw_name:
                continue

            if '-' in raw_name and raw_name.lower() == raw_name:
                raw_name = raw_name.replace('-', ' ')

            category_name = raw_name[:1].upper() + raw_name[1:]
            if category_name not in category_names:
                category_names.append(category_name)

        for category_name in category_names[:6]:
            category_suggestions.append(f'Tư vấn sản phẩm {category_name} đáng mua nhất')

        for category_name in category_names[:4]:
            category_suggestions.append(f'Trong danh mục {category_name}, sản phẩm nào dưới 5 triệu?')

        suggestions = []
        for suggestion in base_suggestions + category_suggestions:
            if suggestion not in suggestions:
                suggestions.append(suggestion)

        if not suggestions:
            suggestions = [
                'Tư vấn sản phẩm phù hợp nhu cầu hàng ngày',
                'Sản phẩm nào đang có giá tốt nhất?',
                'Gợi ý giúp mình vài sản phẩm đáng mua',
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
