"""
RAG Chatbot for product consultation.

This module implements a Retrieval-Augmented Generation (RAG) chatbot that:
1. Extracts search intent from user messages
2. Retrieves relevant products from the database
3. Builds a context with product information
4. Uses Google Gemini API to generate helpful responses
"""

import json
import logging
import os
import re
from decimal import Decimal

import requests
from django.db.models import Q

from .models import Category, Product

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

SYSTEM_PROMPT = """Bạn là trợ lý mua sắm thông minh của cửa hàng thương mại điện tử ShopVN.
Nhiệm vụ của bạn là tư vấn sản phẩm cho khách hàng dựa trên thông tin sản phẩm được cung cấp.

Quy tắc:
1. LUÔN trả lời bằng tiếng Việt
2. Chỉ tư vấn dựa trên sản phẩm có trong danh sách được cung cấp
3. Nếu không tìm thấy sản phẩm phù hợp, hãy nói rõ và gợi ý khách hàng tìm kiếm khác
4. Cung cấp thông tin chi tiết: tên, giá, mô tả, đánh giá, tình trạng kho
5. So sánh sản phẩm khi khách hàng yêu cầu
6. Đưa ra gợi ý phù hợp với nhu cầu, ngân sách của khách hàng
7. Sử dụng emoji để tin nhắn thêm sinh động
8. Giá hiển thị theo VND, format: xxx.xxx₫
9. Khi giới thiệu sản phẩm, hãy thêm slug của sản phẩm theo format [slug:product-slug] để tạo link
10. Trả lời ngắn gọn, tập trung vào thông tin hữu ích, không lan man
"""


def _format_price(price):
    """Format price to Vietnamese VND format."""
    try:
        p = int(Decimal(str(price)))
        return f"{p:,}₫".replace(",", ".")
    except (ValueError, TypeError):
        return str(price)


def _extract_search_keywords(message):
    """Extract search keywords from user message."""
    # Common Vietnamese shopping-related stopwords to remove
    stopwords = {
        'tôi', 'muốn', 'mua', 'tìm', 'cho', 'toi', 'xem', 'giúp', 'giup',
        'có', 'co', 'không', 'khong', 'cái', 'cai', 'nào', 'nao', 'gì', 'gi',
        'bạn', 'ban', 'hãy', 'hay', 'ơi', 'oi', 'nhé', 'nhe', 'đi', 'di',
        'với', 'voi', 'và', 'va', 'của', 'cua', 'này', 'nay', 'đó', 'do',
        'thì', 'thi', 'là', 'la', 'được', 'duoc', 'sản', 'phẩm', 'san', 'pham',
        'giá', 'gia', 'bao', 'nhiêu', 'nhieu', 'rẻ', 're', 'đắt', 'dat',
        'tốt', 'tot', 'nhất', 'nhat', 'cần', 'can', 'kiếm', 'kiem',
        'gợi', 'goi', 'ý', 'y', 'recommend', 'suggest', 'help', 'want',
        'cỡ', 'khoảng', 'khoang', 'dưới', 'duoi', 'trên', 'tren',
        'triệu', 'trieu', 'nghìn', 'nghin', 'đồng', 'dong',
        'loại', 'loai', 'kiểu', 'kieu', 'dạng', 'dang',
        'nên', 'nen', 'thế', 'the', 'sao', 'vậy', 'vay',
        'hỏi', 'hoi', 'xin', 'lỗi', 'loi', 'cảm', 'cam', 'ơn', 'on',
        'chào', 'chao', 'hello', 'hi', 'hey',
        'mình', 'minh', 'em', 'anh', 'chị', 'chi',
        'một', 'mot', 'hai', 'ba', 'các', 'cac', 'những', 'nhung',
        'đấy', 'day', 'kia', 'rồi', 'roi', 'à', 'a', 'ạ',
        'lắm', 'lam', 'quá', 'qua', 'rất', 'rat', 'siêu', 'sieu',
        'tư', 'tu', 'vấn', 'van', 'tư vấn',
    }

    words = message.lower().split()
    keywords = [w for w in words if w not in stopwords and len(w) > 1]
    return keywords


def _extract_price_range(message):
    """Extract price range from user message (in VND)."""
    msg_lower = message.lower()
    min_price = None
    max_price = None

    # Match patterns like "dưới 10 triệu", "under 10tr"
    under_match = re.search(r'(?:dưới|duoi|under|<)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)
    if under_match:
        max_price = float(under_match.group(1).replace(',', '.')) * 1_000_000

    # Match patterns like "trên 5 triệu", "trên 5tr"
    over_match = re.search(r'(?:trên|tren|over|>)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)
    if over_match:
        min_price = float(over_match.group(1).replace(',', '.')) * 1_000_000

    # Match "từ X đến Y triệu"
    range_match = re.search(
        r'(?:từ|tu)\s*(\d+[\.,]?\d*)\s*(?:đến|den|tới|toi|-)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)',
        msg_lower
    )
    if range_match:
        min_price = float(range_match.group(1).replace(',', '.')) * 1_000_000
        max_price = float(range_match.group(2).replace(',', '.')) * 1_000_000

    # Match "khoảng X triệu" (roughly X million)
    approx_match = re.search(r'(?:khoảng|khoang|tầm|tam|~)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)
    if approx_match and not range_match and not under_match and not over_match:
        val = float(approx_match.group(1).replace(',', '.')) * 1_000_000
        min_price = val * 0.7
        max_price = val * 1.3

    return min_price, max_price


def _retrieve_products(message, max_results=15):
    """
    Retrieve relevant products from the database based on the user's message.
    This is the 'Retrieval' part of RAG.
    """
    keywords = _extract_search_keywords(message)
    min_price, max_price = _extract_price_range(message)

    # Build query based on keywords
    query = Q(is_active=True)

    if keywords:
        keyword_query = Q()
        for kw in keywords:
            keyword_query |= (
                Q(name__icontains=kw) |
                Q(description__icontains=kw) |
                Q(category__name__icontains=kw)
            )
        query &= keyword_query

    # Apply price filters
    if min_price is not None:
        query &= Q(price__gte=min_price)
    if max_price is not None:
        query &= Q(price__lte=max_price)

    products = Product.objects.filter(query).select_related('category').order_by('-rating', '-num_reviews')[:max_results]

    # If no keyword match, try to get top products
    if not products.exists() and not keywords:
        products = Product.objects.filter(is_active=True).select_related('category').order_by('-rating', '-num_reviews')[:max_results]

    # If keywords but no results, fall back to broader search
    if not products.exists() and keywords:
        fallback_query = Q(is_active=True)
        for kw in keywords[:2]:
            fallback_query &= (
                Q(name__icontains=kw) |
                Q(description__icontains=kw) |
                Q(category__name__icontains=kw)
            )
        products = Product.objects.filter(fallback_query).select_related('category').order_by('-rating', '-num_reviews')[:max_results]

    return products


def _build_product_context(products):
    """Build a textual context of products for the LLM."""
    if not products:
        return "Không tìm thấy sản phẩm nào phù hợp với yêu cầu."

    context_lines = ["Danh sách sản phẩm tìm được:\n"]

    for i, p in enumerate(products, 1):
        stock_status = "Còn hàng" if p.stock > 0 else "Hết hàng"
        discount = p.discount_percent
        discount_str = f" (Giảm {discount}%)" if discount > 0 else ""

        context_lines.append(
            f"{i}. **{p.name}**\n"
            f"   - Slug: {p.slug}\n"
            f"   - Danh mục: {p.category.name}\n"
            f"   - Giá: {_format_price(p.price)}{discount_str}\n"
            f"   - Giá gốc: {_format_price(p.compare_price) if p.compare_price else 'N/A'}\n"
            f"   - Đánh giá: {p.rating}/5 ⭐ ({p.num_reviews} lượt đánh giá)\n"
            f"   - Tình trạng: {stock_status} ({p.stock} sản phẩm)\n"
            f"   - Mô tả: {p.description}\n"
        )

    return "\n".join(context_lines)


def _build_category_context():
    """Build a context of all available categories."""
    categories = Category.objects.all()
    if not categories:
        return ""

    lines = ["Danh mục sản phẩm có sẵn:"]
    for cat in categories:
        count = cat.products.filter(is_active=True).count()
        lines.append(f"- {cat.name}: {count} sản phẩm")

    return "\n".join(lines)


def generate_chat_response(message, conversation_history=None):
    """
    Generate a chatbot response using RAG (Retrieval-Augmented Generation).

    1. Retrieve relevant products from the database
    2. Build context with product information
    3. Send to Google Gemini API for response generation
    """
    if not GEMINI_API_KEY:
        return _generate_fallback_response(message)

    # Retrieve relevant products
    products = _retrieve_products(message)
    product_context = _build_product_context(products)
    category_context = _build_category_context()

    # Build the full context for the LLM
    rag_context = f"""
{category_context}

{product_context}
"""

    # Build conversation messages
    contents = []

    # Add conversation history if available
    if conversation_history:
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = 'user' if msg.get('role') == 'user' else 'model'
            contents.append({
                'role': role,
                'parts': [{'text': msg.get('content', '')}]
            })

    # Add the current user message with RAG context
    user_message_with_context = f"""
Thông tin sản phẩm từ cơ sở dữ liệu (dùng để tham khảo khi trả lời):
---
{rag_context}
---

Câu hỏi của khách hàng: {message}
"""

    contents.append({
        'role': 'user',
        'parts': [{'text': user_message_with_context}]
    })

    # Call Gemini API
    try:
        response = requests.post(
            f'{GEMINI_API_URL}?key={GEMINI_API_KEY}',
            json={
                'system_instruction': {
                    'parts': [{'text': SYSTEM_PROMPT}]
                },
                'contents': contents,
                'generationConfig': {
                    'temperature': 0.7,
                    'topP': 0.9,
                    'topK': 40,
                    'maxOutputTokens': 1024,
                }
            },
            headers={'Content-Type': 'application/json'},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            if candidates:
                text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text:
                    # Extract product slugs mentioned in the response
                    product_slugs = _extract_product_slugs(text, products)
                    return {
                        'response': text,
                        'products': product_slugs,
                    }

        logger.error('Gemini API error: %s - %s', response.status_code, response.text[:500])
        return _generate_fallback_response(message)

    except requests.RequestException as exc:
        logger.error('Gemini API request failed: %s', exc)
        return _generate_fallback_response(message)


def _extract_product_slugs(response_text, products):
    """Extract product info for products mentioned in the response."""
    mentioned_products = []

    for product in products:
        # Check if product name or slug appears in the response
        if product.name.lower() in response_text.lower() or f'[slug:{product.slug}]' in response_text:
            mentioned_products.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': str(product.price),
                'image_url': product.image_url or '',
                'rating': str(product.rating),
                'category': product.category.name,
            })

    return mentioned_products[:6]  # Limit to 6 product cards


def _generate_fallback_response(message):
    """Generate a fallback response when Gemini API is not available."""
    products = _retrieve_products(message)

    if not products:
        return {
            'response': (
                '🔍 Xin lỗi, mình không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn.\n\n'
                'Bạn có thể thử:\n'
                '- Tìm theo danh mục: Điện thoại, Laptop, Âm thanh, Thời trang...\n'
                '- Tìm theo tên sản phẩm cụ thể\n'
                '- Hỏi theo khoảng giá: "dưới 10 triệu", "từ 5 đến 15 triệu"'
            ),
            'products': [],
        }

    response_lines = ['🛍️ Đây là các sản phẩm mình tìm được cho bạn:\n']

    product_cards = []
    for p in products[:6]:
        response_lines.append(
            f"**{p.name}** — {_format_price(p.price)} "
            f"{'⭐' * int(float(str(p.rating)))} ({p.rating}/5)\n"
            f"_{p.description[:100]}..._\n"
        )
        product_cards.append({
            'id': str(p.id),
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'image_url': p.image_url or '',
            'rating': str(p.rating),
            'category': p.category.name,
        })

    response_lines.append('\n💡 _Lưu ý: Để nhận tư vấn chi tiết hơn, vui lòng cấu hình GEMINI_API_KEY._')

    return {
        'response': '\n'.join(response_lines),
        'products': product_cards,
    }
