"""
RAG (Retrieval-Augmented Generation) engine for product consultation.

This module:
1. Fetches product data from the product-service via REST API
2. Performs intelligent search/filtering based on user intent
3. Builds context from retrieved products
4. Sends to Google Gemini API to generate helpful responses in Vietnamese
"""

import logging
import os
import re
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'

SYSTEM_PROMPT = """Bạn là trợ lý mua sắm thông minh của cửa hàng thương mại điện tử ShopVN.
Nhiệm vụ của bạn là tư vấn sản phẩm cho khách hàng dựa trên thông tin sản phẩm được cung cấp.

Quy tắc:
1. LUÔN trả lời bằng tiếng Việt
2. Chỉ tư vấn dựa trên sản phẩm có trong danh sách được cung cấp
3. Nếu không tìm thấy sản phẩm phù hợp, hãy nói rõ và gợi ý khách hàng tìm kiếm khác
4. Cung cấp thông tin chi tiết: tên, giá, mô tả, đánh giá, tình trạng kho
5. So sánh sản phẩm khi khách hàng yêu cầu
6. Đưa ra gợi ý phù hợp với nhu cầu và ngân sách của khách hàng
7. Sử dụng emoji phù hợp để tin nhắn thêm sinh động
8. Giá hiển thị theo VND, format: xxx.xxx₫
9. Khi đề cập sản phẩm, hãy nhắc tên chính xác để hệ thống có thể tạo link
10. Trả lời ngắn gọn, tập trung vào thông tin hữu ích
11. Nếu khách chào hỏi, hãy chào lại thân thiện và hỏi họ cần tư vấn gì
12. Giới thiệu tối đa 4-5 sản phẩm mỗi lần trả lời, không liệt kê quá nhiều
"""


def _format_price(price):
    """Format price to Vietnamese VND format."""
    try:
        p = int(Decimal(str(price)))
        return f"{p:,}₫".replace(",", ".")
    except (ValueError, TypeError):
        return str(price)


def _extract_search_params(message):
    """
    Extract search parameters from user message.
    Returns a dict of query params for the product-service API.
    """
    params = {}
    msg_lower = message.lower()

    # Extract search keywords (remove Vietnamese stopwords)
    stopwords = {
        'tôi', 'muốn', 'mua', 'tìm', 'cho', 'toi', 'xem', 'giúp', 'giup',
        'có', 'co', 'không', 'khong', 'cái', 'cai', 'nào', 'nao', 'gì', 'gi',
        'bạn', 'ban', 'hãy', 'hay', 'ơi', 'oi', 'nhé', 'nhe', 'đi', 'di',
        'với', 'voi', 'và', 'va', 'của', 'cua', 'này', 'nay', 'đó', 'do',
        'thì', 'thi', 'là', 'la', 'được', 'duoc', 'sản', 'phẩm', 'san', 'pham',
        'giá', 'gia', 'bao', 'nhiêu', 'nhieu', 'rẻ', 're', 'đắt', 'dat',
        'tốt', 'tot', 'nhất', 'nhat', 'cần', 'can', 'kiếm', 'kiem',
        'nên', 'nen', 'thế', 'the', 'sao', 'vậy', 'vay',
        'hỏi', 'hoi', 'xin', 'lỗi', 'loi', 'cảm', 'cam', 'ơn', 'on',
        'chào', 'chao', 'hello', 'hi', 'hey',
        'mình', 'minh', 'em', 'anh', 'chị', 'chi',
        'một', 'mot', 'hai', 'ba', 'các', 'cac', 'những', 'nhung',
        'đấy', 'day', 'kia', 'rồi', 'roi', 'à', 'a', 'ạ',
        'lắm', 'lam', 'quá', 'qua', 'rất', 'rat', 'siêu', 'sieu',
        'tư', 'tu', 'vấn', 'van', 'gợi', 'goi', 'ý', 'y',
        'recommend', 'suggest', 'help', 'want',
        'loại', 'loai', 'kiểu', 'kieu', 'dạng', 'dang',
    }

    words = msg_lower.split()
    keywords = [w for w in words if w not in stopwords and len(w) > 1]
    if keywords:
        params['search'] = ' '.join(keywords)

    # Extract price range
    under_match = re.search(r'(?:dưới|duoi|under|<)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)
    over_match = re.search(r'(?:trên|tren|over|>)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)
    range_match = re.search(
        r'(?:từ|tu)\s*(\d+[\.,]?\d*)\s*(?:đến|den|tới|toi|-)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)',
        msg_lower
    )
    approx_match = re.search(r'(?:khoảng|khoang|tầm|tam|~)\s*(\d+[\.,]?\d*)\s*(?:triệu|tr|trieu)', msg_lower)

    if range_match:
        params['price_min'] = float(range_match.group(1).replace(',', '.')) * 1_000_000
        params['price_max'] = float(range_match.group(2).replace(',', '.')) * 1_000_000
    elif under_match:
        params['price_max'] = float(under_match.group(1).replace(',', '.')) * 1_000_000
    elif over_match:
        params['price_min'] = float(over_match.group(1).replace(',', '.')) * 1_000_000
    elif approx_match:
        val = float(approx_match.group(1).replace(',', '.')) * 1_000_000
        params['price_min'] = val * 0.7
        params['price_max'] = val * 1.3

    # Sorting
    if any(kw in msg_lower for kw in ['rẻ nhất', 're nhat', 'giá thấp', 'gia thap', 'tiết kiệm']):
        params['ordering'] = 'price'
    elif any(kw in msg_lower for kw in ['đắt nhất', 'dat nhat', 'giá cao', 'gia cao', 'cao cấp']):
        params['ordering'] = '-price'
    elif any(kw in msg_lower for kw in ['đánh giá', 'danh gia', 'tốt nhất', 'tot nhat', 'phổ biến']):
        params['ordering'] = '-rating'

    return params


def _fetch_products(search_params):
    """Fetch products from product-service API."""
    product_service_url = settings.PRODUCT_SERVICE_URL
    url = f'{product_service_url}/products/'

    # Build query params for the product-service API
    query_params = {}
    if 'search' in search_params:
        query_params['search'] = search_params['search']
    if 'ordering' in search_params:
        query_params['ordering'] = search_params['ordering']
    if 'category' in search_params:
        query_params['category'] = search_params['category']

    # Increase page size for better context
    query_params['page_size'] = 20

    try:
        resp = requests.get(url, params=query_params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', data) if isinstance(data, dict) else data

            # Apply price filtering client-side (product-service may not support it)
            price_min = search_params.get('price_min')
            price_max = search_params.get('price_max')

            if price_min or price_max:
                filtered = []
                for p in results:
                    price = float(p.get('price', 0))
                    if price_min and price < price_min:
                        continue
                    if price_max and price > price_max:
                        continue
                    filtered.append(p)
                results = filtered

            return results
        else:
            logger.error('Product service returned %s: %s', resp.status_code, resp.text[:300])
            return []
    except requests.RequestException as exc:
        logger.error('Failed to fetch products from product-service: %s', exc)
        return []


def _fetch_categories():
    """Fetch categories from product-service API."""
    product_service_url = settings.PRODUCT_SERVICE_URL
    url = f'{product_service_url}/products/categories/'

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except requests.RequestException as exc:
        logger.error('Failed to fetch categories: %s', exc)
        return []


def _build_product_context(products):
    """Build a textual context of products for the LLM."""
    if not products:
        return "Không tìm thấy sản phẩm nào phù hợp với yêu cầu."

    context_lines = ["Danh sách sản phẩm tìm được:\n"]

    for i, p in enumerate(products[:15], 1):
        price = _format_price(p.get('price', 0))
        compare_price = p.get('compare_price')
        compare_str = f" (Giá gốc: {_format_price(compare_price)})" if compare_price else ""
        discount = p.get('discount_percent', 0)
        discount_str = f" — Giảm {discount}%" if discount else ""
        stock = p.get('stock', 0)
        stock_status = "Còn hàng" if stock > 0 else "Hết hàng"
        rating = p.get('rating', 0)
        num_reviews = p.get('num_reviews', 0)
        cat_name = p.get('category_name', 'N/A')

        context_lines.append(
            f"{i}. **{p.get('name', 'N/A')}**\n"
            f"   - Slug: {p.get('slug', '')}\n"
            f"   - Danh mục: {cat_name}\n"
            f"   - Giá: {price}{compare_str}{discount_str}\n"
            f"   - Đánh giá: {rating}/5 ⭐ ({num_reviews} lượt)\n"
            f"   - Tình trạng: {stock_status} ({stock} sp)\n"
        )

    return "\n".join(context_lines)


def _build_category_context(categories):
    """Build a context of all available categories."""
    if not categories:
        return ""

    lines = ["Danh mục sản phẩm có sẵn:"]
    for cat in categories:
        count = cat.get('product_count', 0)
        lines.append(f"- {cat.get('name', 'N/A')}: {count} sản phẩm")

    return "\n".join(lines)


def _extract_mentioned_products(response_text, products):
    """Extract product info for products mentioned in the response."""
    mentioned = []

    for product in products[:15]:
        name = product.get('name', '')
        if name and name.lower() in response_text.lower():
            mentioned.append({
                'id': str(product.get('id', '')),
                'name': name,
                'slug': product.get('slug', ''),
                'price': str(product.get('price', '')),
                'compare_price': str(product.get('compare_price', '')) if product.get('compare_price') else None,
                'image_url': product.get('image_url', ''),
                'rating': str(product.get('rating', '')),
                'num_reviews': product.get('num_reviews', 0),
                'category_name': product.get('category_name', ''),
                'discount_percent': product.get('discount_percent', 0),
            })

    return mentioned[:6]


def generate_response(message, conversation_history=None):
    """
    Main RAG pipeline:
    1. Extract search intent from message
    2. Retrieve products from product-service
    3. Build context
    4. Generate response with Gemini API
    """
    # Step 1: Extract search parameters
    search_params = _extract_search_params(message)

    # Step 2: Retrieve products and categories
    products = _fetch_products(search_params)
    categories = _fetch_categories()

    # Step 3: Build context
    product_context = _build_product_context(products)
    category_context = _build_category_context(categories)

    rag_context = f"{category_context}\n\n{product_context}"

    # Step 4: Generate response
    if not GEMINI_API_KEY:
        return _fallback_response(products)

    return _call_gemini(message, rag_context, products, conversation_history)


def _call_gemini(message, rag_context, products, conversation_history=None):
    """Call Google Gemini API to generate a response."""

    # Build conversation contents
    contents = []

    # Add conversation history (last 8 messages)
    if conversation_history:
        for msg in conversation_history[-8:]:
            role = 'user' if msg.get('role') == 'user' else 'model'
            contents.append({
                'role': role,
                'parts': [{'text': msg.get('content', '')}]
            })

    # Add current message with RAG context
    user_message = f"""
Thông tin sản phẩm từ cơ sở dữ liệu (dùng để tham khảo khi trả lời):
---
{rag_context}
---

Câu hỏi của khách hàng: {message}
"""

    contents.append({
        'role': 'user',
        'parts': [{'text': user_message}]
    })

    try:
        resp = requests.post(
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

        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get('candidates', [])
            if candidates:
                text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text:
                    mentioned = _extract_mentioned_products(text, products)
                    return {
                        'response': text,
                        'products': mentioned,
                    }

        logger.error('Gemini API error %s: %s', resp.status_code, resp.text[:500])
        return _fallback_response(products)

    except requests.RequestException as exc:
        logger.error('Gemini API request failed: %s', exc)
        return _fallback_response(products)


def _fallback_response(products):
    """Generate a fallback response when Gemini API is unavailable."""
    if not products:
        return {
            'response': (
                '🔍 Xin lỗi, mình không tìm thấy sản phẩm nào phù hợp.\n\n'
                'Bạn có thể thử:\n'
                '• Tìm theo danh mục: Điện thoại, Laptop, Âm thanh, Thời trang...\n'
                '• Tìm theo tên sản phẩm cụ thể\n'
                '• Hỏi theo khoảng giá: "dưới 10 triệu", "từ 5 đến 15 triệu"'
            ),
            'products': [],
        }

    response_lines = ['🛍️ Đây là các sản phẩm mình tìm được:\n']
    product_cards = []

    for p in products[:5]:
        name = p.get('name', '')
        price = _format_price(p.get('price', 0))
        rating = p.get('rating', 0)

        response_lines.append(f"• **{name}** — {price} ⭐ {rating}/5")

        product_cards.append({
            'id': str(p.get('id', '')),
            'name': name,
            'slug': p.get('slug', ''),
            'price': str(p.get('price', '')),
            'compare_price': str(p.get('compare_price', '')) if p.get('compare_price') else None,
            'image_url': p.get('image_url', ''),
            'rating': str(p.get('rating', '')),
            'num_reviews': p.get('num_reviews', 0),
            'category_name': p.get('category_name', ''),
            'discount_percent': p.get('discount_percent', 0),
        })

    response_lines.append('\n💡 _Cấu hình GEMINI_API_KEY để nhận tư vấn chi tiết hơn._')

    return {
        'response': '\n'.join(response_lines),
        'products': product_cards,
    }
