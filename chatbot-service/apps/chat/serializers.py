from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'product_refs', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'session_id', 'user_id', 'messages', 'message_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    """Validates incoming chat requests."""
    message = serializers.CharField(max_length=2000, help_text='User message text')
    session_id = serializers.CharField(max_length=255, help_text='Browser session identifier')
    conversation_id = serializers.UUIDField(required=False, help_text='Existing conversation ID to continue')


class ChatResponseSerializer(serializers.Serializer):
    """Shape of the chat response."""
    conversation_id = serializers.UUIDField()
    response = serializers.CharField()
    product_refs = serializers.ListField(child=serializers.CharField())
    products = serializers.ListField(child=serializers.DictField(), required=False)
