"""
Knowledge Base Module
---------------------
Xây dựng Knowledge Base cho RAG Chatbot bằng cách:
- Fetch toàn bộ sản phẩm từ Product Service API
- Chuyển đổi thành document text cho embedding
- Chuẩn bị metadata để lưu vào ChromaDB
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def fetch_all_products():
    """
    Fetch all active products from the product-service.
    Handles pagination automatically (page_size=100).
    Returns a list of product dicts.
    """
    products = []
    page = 1
    base_url = f'{settings.PRODUCT_SERVICE_URL}/products/'

    while True:
        try:
            resp = requests.get(
                base_url,
                params={'page': page, 'page_size': 100},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get('results', data) if isinstance(data, dict) else data
            if not results:
                break

            products.extend(results)

            # Check if there's a next page
            if isinstance(data, dict) and data.get('next'):
                page += 1
            else:
                break
        except requests.RequestException as e:
            logger.error(f'Error fetching products (page {page}): {e}')
            break

    logger.info(f'Fetched {len(products)} products from product-service')
    return products


def fetch_all_categories():
    """Fetch all categories from the product-service."""
    try:
        resp = requests.get(
            f'{settings.PRODUCT_SERVICE_URL}/products/categories/',
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        return results
    except requests.RequestException as e:
        logger.error(f'Error fetching categories: {e}')
        return []


def build_product_document(product):
    """
    Convert a product dict into a text document for embedding.
    Includes all relevant fields that a customer might ask about.
    """
    category_name = product.get('category_name', '')
    if not category_name and isinstance(product.get('category'), dict):
        category_name = product['category'].get('name', '')

    price = product.get('price', 0)
    compare_price = product.get('compare_price')
    stock = product.get('stock', 0)
    rating = product.get('rating', 0)
    num_reviews = product.get('num_reviews', 0)

    # Format price to Vietnamese style
    try:
        price_formatted = f"{int(float(price)):,}".replace(',', '.') + 'đ'
    except (ValueError, TypeError):
        price_formatted = str(price)

    discount_info = ''
    if compare_price and float(compare_price) > float(price):
        try:
            compare_formatted = f"{int(float(compare_price)):,}".replace(',', '.') + 'đ'
            discount_pct = round((1 - float(price) / float(compare_price)) * 100)
            discount_info = f' (giá gốc: {compare_formatted}, giảm {discount_pct}%)'
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    stock_status = 'Còn hàng' if stock > 0 else 'Hết hàng'

    doc = (
        f"Sản phẩm: {product.get('name', '')}\n"
        f"Danh mục: {category_name}\n"
        f"Mô tả: {product.get('description', '')}\n"
        f"Giá bán: {price_formatted}{discount_info}\n"
        f"Đánh giá: {rating}/5 ({num_reviews} đánh giá)\n"
        f"Tình trạng: {stock_status} (còn {stock} sản phẩm)\n"
        f"Slug: {product.get('slug', '')}"
    )
    return doc


def build_product_metadata(product):
    """Build metadata dict for ChromaDB storage."""
    category_name = product.get('category_name', '')
    if not category_name and isinstance(product.get('category'), dict):
        category_name = product['category'].get('name', '')

    return {
        'product_id': str(product.get('id', '')),
        'name': str(product.get('name', '')),
        'category': category_name,
        'price': float(product.get('price', 0)),
        'stock': int(product.get('stock', 0)),
        'rating': float(product.get('rating', 0)),
        'slug': str(product.get('slug', '')),
        'image_url': str(product.get('image_url', '')),
        'is_in_stock': product.get('stock', 0) > 0,
    }
