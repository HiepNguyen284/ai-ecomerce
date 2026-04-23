"""
RAG (Retrieval Augmented Generation) Engine backed by Neo4j KB Graph.

Flow:
1. User sends a question (Vietnamese or English)
2. Intent detection → classify question type
3. Cypher query generation → retrieve relevant subgraph from Neo4j
4. Context assembly → format retrieved data
5. Response generation → generate natural language answer

Supported intents:
- product_search: Search products by name/category keyword
- recommend:      Product recommendations for a user
- user_info:      User behavior analysis
- product_info:   Product popularity / who interacted
- similar:        Similar users
- category:       Category statistics
- funnel:         Funnel / conversion analysis
- stats:          Overall statistics
- general:        General / greeting questions
"""

import os
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def _get_neo4j_driver():
    """Create Neo4j driver."""
    from neo4j import GraphDatabase
    uri = os.environ.get('NEO4J_URI', 'bolt://neo4j-db:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'password')
    return GraphDatabase.driver(uri, auth=(user, password))


# ──────────────────────────────────────────────
# Intent Detection
# ──────────────────────────────────────────────

INTENT_PATTERNS = {
    'product_search': [
        r'muốn mua', r'tìm mua', r'mua\b', r'cần mua',
        r'cho (?:tôi )?xem', r'tìm.*(?:sản phẩm|hàng)',
        r'có bán', r'có không', r'giá.*bao nhiêu',
        r'tìm kiếm', r'search', r'find', r'looking for',
        r'i want', r'buy', r'shop for', r'where.*can.*get',
        r'show me', r'cho xem', r'xem.*(?:sản phẩm|hàng)',
        r'tư vấn.*mua', r'muốn tìm', r'cần tìm',
        r'có.*(?:loại|kiểu|mẫu)', r'bán.*gì',
    ],
    'recommend': [
        r'gợi ý', r'đề xuất', r'recommend', r'suggest',
        r'nên mua', r'sản phẩm phù hợp', r'phù hợp với',
        r'mua gì', r'xem gì', r'thích gì',
        r'gợi ý.*cho.*user', r'recommend.*user',
    ],
    'user_info': [
        r'hành vi.*user', r'user.*hành vi', r'thông tin.*user',
        r'user.*làm gì', r'user.*mua', r'người dùng.*hành vi',
        r'user behavior', r'what.*user.*do', r'user profile',
        r'hoạt động.*user', r'user.*hoạt động',
    ],
    'product_info': [
        r'sản phẩm.*phổ biến', r'top.*sản phẩm', r'product.*popular',
        r'bán chạy', r'nhiều người.*mua', r'sản phẩm nào.*hot',
        r'ai.*mua.*sản phẩm', r'who.*bought', r'product info',
        r'top.*bán', r'best.*sell',
    ],
    'similar': [
        r'tương tự', r'giống', r'similar', r'like.*user',
        r'cùng sở thích', r'same.*interest', r'người.*giống',
    ],
    'category': [
        r'danh mục', r'category', r'loại.*sản phẩm', r'thể loại',
        r'ngành hàng', r'phân loại', r'category.*stats',
    ],
    'funnel': [
        r'funnel', r'chuyển đổi', r'conversion', r'phễu',
        r'tỷ lệ.*mua', r'view.*purchase', r'hành trình',
    ],
    'stats': [
        r'thống kê', r'tổng quan', r'overview', r'statistics',
        r'bao nhiêu', r'tổng', r'how many', r'summary',
        r'tình hình', r'báo cáo', r'report',
    ],
}


def detect_intent(question):
    """Detect user intent from natural language question."""
    q = question.lower().strip()

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, q):
                return intent

    return 'general'


def extract_user_ref(question):
    """Extract user UUID or username reference from question."""
    # UUID pattern
    uuid_match = re.search(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        question, re.IGNORECASE)
    if uuid_match:
        return uuid_match.group(0)

    # Username pattern (user1, user123, etc.)
    user_match = re.search(r'user\s*(\d+)', question, re.IGNORECASE)
    if user_match:
        return f'user{user_match.group(1)}'

    return None


def extract_product_keyword(question):
    """Extract product name or category keyword from a natural language query."""
    q = question.lower().strip()

    # Phrase-based removal (longest match first, whole phrases only)
    phrases_to_remove = [
        'cho tôi xem', 'cho xem', 'tôi muốn mua', 'tôi muốn tìm',
        'tôi cần mua', 'tôi cần tìm', 'muốn mua', 'muốn tìm',
        'cần mua', 'cần tìm', 'tìm mua', 'tìm kiếm',
        'có bán', 'có không', 'giá bao nhiêu', 'bao nhiêu',
        'sản phẩm', 'hàng hóa', 'ở đâu', 'được không',
        'giúp tôi', 'cho tôi', 'tôi', 'mình', 'em',
        'muốn', 'cần', 'hãy', 'giúp', 'với', 'nhé', 'ạ', 'nào',
        'i want to buy', 'i want to find', 'i want', 'i need',
        'show me', 'find me', 'looking for', 'search for',
        'where can i get', 'where can i buy',
        'find', 'search', 'show', 'buy', 'get',
    ]

    keyword = q
    for phrase in phrases_to_remove:
        # Only remove as whole word/phrase (word boundary)
        keyword = re.sub(r'\b' + re.escape(phrase) + r'\b', ' ', keyword)

    keyword = re.sub(r'\s+', ' ', keyword).strip().strip('?!.,;: ')

    # If nothing meaningful left, take last meaningful word(s)
    if not keyword or len(keyword) < 2:
        words = q.split()
        keyword = words[-1] if words else q

    return keyword


# Vietnamese → English keyword translation for KB Graph search
VI_TO_EN_MAP = {
    'điện thoại': 'phone',
    'dt': 'phone',
    'dien thoai': 'phone',
    'smartphone': 'phone',
    'iphone': 'iphone',
    'samsung': 'samsung',
    'máy tính': 'laptop',
    'may tinh': 'laptop',
    'laptop': 'laptop',
    'quần áo': 'shirt',
    'quan ao': 'shirt',
    'áo': 'shirt',
    'quần': 'shirt',
    'giày': 'shoe',
    'giay': 'shoe',
    'dép': 'slipper',
    'dep': 'slipper',
    'đồng hồ': 'watch',
    'dong ho': 'watch',
    'nước hoa': 'fragrance',
    'nuoc hoa': 'fragrance',
    'mỹ phẩm': 'beauty',
    'my pham': 'beauty',
    'son môi': 'beauty',
    'nội thất': 'furniture',
    'noi that': 'furniture',
    'bàn': 'table',
    'ghế': 'chair',
    'giường': 'bed',
    'trang trí': 'decoration',
    'trang tri': 'decoration',
    'thực phẩm': 'groceries',
    'thuc pham': 'groceries',
    'đồ ăn': 'groceries',
    'do an': 'groceries',
    'trái cây': 'fruit',
    'trai cay': 'fruit',
    'xe máy': 'motorcycle',
    'xe may': 'motorcycle',
    'ô tô': 'vehicle',
    'o to': 'vehicle',
    'xe': 'vehicle',
    'kính': 'glasses',
    'kinh': 'glasses',
    'túi': 'bag',
    'balo': 'bag',
    'nhẫn': 'ring',
    'trang sức': 'jewel',
    'trang suc': 'jewel',
    'đèn': 'light',
    'den': 'lamp',
    'nhà bếp': 'kitchen',
    'nha bep': 'kitchen',
}


def _translate_keyword(keyword):
    """Translate Vietnamese keyword to English for KB Graph search."""
    kw = keyword.lower().strip()

    # Direct match
    if kw in VI_TO_EN_MAP:
        return VI_TO_EN_MAP[kw]

    # Check if any Vietnamese key is contained in the keyword
    for vi, en in VI_TO_EN_MAP.items():
        if vi in kw:
            return en

    return keyword


def retrieve_products_by_keyword(driver, keyword, limit=8):
    """Search products in KB Graph by name or category keyword."""
    with driver.session() as session:
        kw = keyword.strip()
        en_kw = _translate_keyword(kw)

        # Build search terms list (original + translated)
        search_terms = [kw]
        if en_kw != kw:
            search_terms.append(en_kw)

        # Search by product name or category (case-insensitive CONTAINS)
        # Try each search term until we find results
        products = []
        for term in search_terms:
            result = session.run("""
                MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                WHERE toLower(p.name) CONTAINS toLower($kw)
                   OR toLower(c.name) CONTAINS toLower($kw)
                OPTIONAL MATCH (buyer:User)-[:PURCHASED]->(p)
                WITH p, c, count(DISTINCT buyer) AS buyers
                OPTIONAL MATCH (viewer:User)-[:VIEWED]->(p)
                WITH p, c, buyers, count(DISTINCT viewer) AS viewers
                RETURN p.name AS product, p.price AS price,
                       p.slug AS slug, c.name AS category,
                       buyers, viewers
                ORDER BY buyers DESC, viewers DESC
                LIMIT $limit
            """, kw=term, limit=limit)
            products = [dict(r) for r in result]
            if products:
                break

        return {'keyword': kw, 'products': products}


def retrieve_similar_users(driver, user_ref, limit=5):
    """Retrieve similar users from graph."""
    with driver.session() as session:
        user = _find_user(session, user_ref)
        if not user:
            return None, "Không tìm thấy người dùng."

        result = session.run("""
            MATCH (u:User {uuid: $uuid})-[r:SIMILAR_TO]->(s:User)
            OPTIONAL MATCH (s)-[:PURCHASED]->(p:Product)
            WITH s, r.score AS similarity, count(DISTINCT p) AS purchases
            RETURN s.username AS username, s.type AS type,
                   similarity, purchases, s.total_actions AS total_actions
            ORDER BY similarity DESC
            LIMIT $limit
        """, uuid=user['uuid'], limit=limit)
        similars = [dict(r) for r in result]

        return {'user': user, 'similar_users': similars}, None


def retrieve_category_stats(driver):
    """Retrieve category-level statistics."""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Category)<-[:BELONGS_TO]-(p:Product)
            OPTIONAL MATCH (u:User)-[:PURCHASED]->(p)
            WITH c, count(DISTINCT p) AS products, count(DISTINCT u) AS buyers
            OPTIONAL MATCH (viewer:User)-[:VIEWED]->(p2:Product)
                          -[:BELONGS_TO]->(c)
            WITH c, products, buyers, count(DISTINCT viewer) AS viewers
            RETURN c.name AS category, products, buyers, viewers
            ORDER BY buyers DESC
        """)
        return [dict(r) for r in result]


def retrieve_funnel(driver):
    """Retrieve funnel conversion data from graph."""
    with driver.session() as session:
        stages = ['VIEWED', 'CLICKED', 'SEARCHED', 'ADDED_TO_CART',
                  'ADDED_TO_WISHLIST', 'PURCHASED', 'REVIEWED', 'SHARED']
        funnel = []
        for rel_type in stages:
            result = session.run(f"""
                MATCH (u:User)-[:{rel_type}]->(:Product)
                RETURN count(DISTINCT u) AS users
            """)
            count = result.single()['users']
            funnel.append({'stage': rel_type, 'users': count})
        return funnel


def retrieve_stats(driver):
    """Retrieve overall graph statistics."""
    with driver.session() as session:
        stats = {}

        result = session.run("MATCH (u:User) RETURN count(u) AS c")
        stats['total_users'] = result.single()['c']

        result = session.run("MATCH (p:Product) RETURN count(p) AS c")
        stats['total_products'] = result.single()['c']

        result = session.run("MATCH (c:Category) RETURN count(c) AS c")
        stats['total_categories'] = result.single()['c']

        result = session.run("MATCH ()-[r]->() RETURN count(r) AS c")
        stats['total_relationships'] = result.single()['c']

        result = session.run("""
            MATCH (u:User)-[:PURCHASED]->(:Product)
            RETURN count(DISTINCT u) AS buyers
        """)
        stats['users_who_purchased'] = result.single()['buyers']

        # User type distribution
        result = session.run("""
            MATCH (u:User)
            RETURN u.type AS type, count(u) AS count
            ORDER BY count DESC
        """)
        stats['user_types'] = [dict(r) for r in result]

        # Top categories
        result = session.run("""
            MATCH (:User)-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
            RETURN c.name AS category, count(*) AS purchases
            ORDER BY purchases DESC
            LIMIT 5
        """)
        stats['top_categories'] = [dict(r) for r in result]

        return stats


def _find_user(session, user_ref):
    """Find user by UUID or username."""
    if not user_ref:
        # Return a random user
        result = session.run("""
            MATCH (u:User)
            RETURN u.uuid AS uuid, u.username AS username,
                   u.type AS type, u.total_actions AS total_actions
            LIMIT 1
        """)
        record = result.single()
        return dict(record) if record else None

    # Try UUID first
    result = session.run("""
        MATCH (u:User {uuid: $ref})
        RETURN u.uuid AS uuid, u.username AS username,
               u.type AS type, u.total_actions AS total_actions
    """, ref=user_ref)
    record = result.single()
    if record:
        return dict(record)

    # Try username
    result = session.run("""
        MATCH (u:User)
        WHERE u.username = $ref OR u.username CONTAINS $ref
        RETURN u.uuid AS uuid, u.username AS username,
               u.type AS type, u.total_actions AS total_actions
        LIMIT 1
    """, ref=user_ref)
    record = result.single()
    if record:
        return dict(record)

    return None


# ──────────────────────────────────────────────
# Response Generation
# ──────────────────────────────────────────────

def generate_response(intent, context, question):
    """Generate a natural language response from retrieved context."""

    if intent == 'product_search':
        return _format_product_search(context)
    elif intent == 'recommend':
        return _format_recommendation(context)
    elif intent == 'user_info':
        return _format_user_info(context)
    elif intent == 'product_info':
        return _format_product_info(context)
    elif intent == 'similar':
        return _format_similar_users(context)
    elif intent == 'category':
        return _format_category_stats(context)
    elif intent == 'funnel':
        return _format_funnel(context)
    elif intent == 'stats':
        return _format_stats(context)
    else:
        return _format_general(context)


def _format_product_search(ctx):
    """Format product search results."""
    if not ctx or not ctx.get('products'):
        kw = ctx.get('keyword', '') if ctx else ''
        return (f"🔍 Không tìm thấy sản phẩm nào khớp với **\"{kw}\"** "
                f"trong Knowledge Graph.\n\n"
                f"💡 Thử tìm với từ khóa khác, ví dụ:\n"
                f"  - _\"Tìm laptop\"_\n"
                f"  - _\"Cho xem điện thoại\"_\n"
                f"  - _\"Muốn mua giày\"_")

    kw = ctx['keyword']
    products = ctx['products']
    lines = [f"🔍 **Kết quả tìm kiếm cho \"{kw}\"** — "
             f"Tìm thấy **{len(products)}** sản phẩm từ Knowledge Graph\n"]

    for i, p in enumerate(products, 1):
        price_str = f"{p['price']:,.0f}đ" if p.get('price') else "Liên hệ"
        lines.append(f"  {i}. **{p['product']}** — {price_str}")
        lines.append(f"     📁 {p['category']} | "
                     f"🛒 {p.get('buyers', 0)} người mua | "
                     f"👁 {p.get('viewers', 0)} lượt xem")
        lines.append("")

    lines.append("💡 *Dữ liệu từ Neo4j Knowledge Base Graph — "
                 "xếp hạng theo số người đã mua.*")
    return "\n".join(lines)


def _format_recommendation(ctx):
    if not ctx or not ctx.get('recommendations'):
        return ("Hiện tại chưa có đủ dữ liệu để gợi ý sản phẩm cho người dùng này. "
                "Hãy thử tương tác thêm để hệ thống hiểu rõ sở thích của bạn!")

    user = ctx['user']
    recs = ctx['recommendations']
    lines = [f"🛒 **Gợi ý sản phẩm cho {user['username']}** (Loại: {user['type']})\n"]
    lines.append("Dựa trên phân tích Knowledge Graph, đây là các sản phẩm phù hợp:\n")

    for i, r in enumerate(recs, 1):
        price = f"${r['price']:.2f}" if r.get('price') else "N/A"
        lines.append(f"  {i}. **{r['product']}** — {price}")
        lines.append(f"     📁 Danh mục: {r['category']}")
        lines.append(f"     👥 {r['recommenders']} người dùng tương tự đã mua\n")

    lines.append("💡 *Gợi ý dựa trên hành vi mua hàng của người dùng có sở thích tương tự.*")
    return "\n".join(lines)


def _format_user_info(ctx):
    if not ctx:
        return "Không tìm thấy thông tin người dùng."

    user = ctx['user']
    lines = [f"👤 **Phân tích hành vi: {user['username']}**\n"]
    lines.append(f"  - Loại: **{user['type']}**")
    lines.append(f"  - Tổng hành động: **{user['total_actions']}**\n")

    if ctx.get('actions'):
        lines.append("📊 **Phân bố hành vi:**")
        for a in ctx['actions']:
            bar = '█' * min(int(a['count'] / 5), 20)
            lines.append(f"  {a['action']:>18s}: {a['count']:>4d} {bar}")
        lines.append("")

    if ctx.get('top_categories'):
        lines.append("📁 **Danh mục yêu thích:**")
        for c in ctx['top_categories']:
            lines.append(f"  - {c['category']}: {c['interaction_count']} tương tác")
        lines.append("")

    return "\n".join(lines)


def _format_product_info(ctx):
    if not ctx:
        return "Không có dữ liệu sản phẩm."

    lines = ["🏆 **Top sản phẩm phổ biến nhất**\n"]
    for i, p in enumerate(ctx, 1):
        price = f"${p['price']:.2f}" if p.get('price') else "N/A"
        lines.append(f"  {i}. **{p['product']}** — {price}")
        lines.append(f"     📁 {p['category']} | 🛒 {p['buyers']} người mua | 👁 {p['viewers']} lượt xem\n")

    return "\n".join(lines)


def _format_similar_users(ctx):
    if not ctx or not ctx.get('similar_users'):
        return "Không tìm thấy người dùng tương tự."

    user = ctx['user']
    lines = [f"👥 **Người dùng tương tự với {user['username']}**\n"]

    for s in ctx['similar_users']:
        sim_pct = f"{s['similarity'] * 100:.1f}%"
        lines.append(f"  - **{s['username']}** ({s['type']})")
        lines.append(f"    Độ tương đồng: {sim_pct} | "
                     f"Đã mua: {s['purchases']} SP | "
                     f"Tổng HĐ: {s['total_actions']}\n")

    lines.append("💡 *Tương đồng tính bằng Jaccard Similarity trên tập sản phẩm đã tương tác.*")
    return "\n".join(lines)


def _format_category_stats(ctx):
    if not ctx:
        return "Không có dữ liệu danh mục."

    lines = ["📁 **Thống kê theo danh mục sản phẩm**\n"]
    lines.append(f"{'Danh mục':<25s} {'SP':>5s} {'Người mua':>10s} {'Lượt xem':>10s}")
    lines.append("-" * 55)

    for c in ctx:
        lines.append(f"{c['category']:<25s} {c['products']:>5d} "
                     f"{c['buyers']:>10d} {c['viewers']:>10d}")

    return "\n".join(lines)


def _format_funnel(ctx):
    if not ctx:
        return "Không có dữ liệu funnel."

    lines = ["📈 **Phân tích Funnel chuyển đổi**\n"]
    max_users = ctx[0]['users'] if ctx else 1

    for i, stage in enumerate(ctx):
        pct = stage['users'] / max_users * 100
        bar = '█' * int(pct / 3)
        conv = ""
        if i > 0 and ctx[i - 1]['users'] > 0:
            conv_rate = stage['users'] / ctx[i - 1]['users'] * 100
            conv = f" (↓{conv_rate:.1f}%)"
        lines.append(f"  {stage['stage']:>20s}: {stage['users']:>4d} users "
                     f"({pct:5.1f}%) {bar}{conv}")

    lines.append(f"\n💡 *Tổng {max_users} người dùng bắt đầu từ VIEWED.*")
    return "\n".join(lines)


def _format_stats(ctx):
    if not ctx:
        return "Không có dữ liệu thống kê."

    lines = ["📊 **Tổng quan Knowledge Base Graph**\n"]
    lines.append(f"  👥 Tổng người dùng:     **{ctx['total_users']}**")
    lines.append(f"  📦 Tổng sản phẩm:       **{ctx['total_products']}**")
    lines.append(f"  📁 Tổng danh mục:       **{ctx['total_categories']}**")
    lines.append(f"  🔗 Tổng quan hệ:        **{ctx['total_relationships']}**")
    lines.append(f"  🛒 Người đã mua hàng:   **{ctx['users_who_purchased']}**")
    lines.append("")

    if ctx.get('user_types'):
        lines.append("👤 **Phân loại người dùng:**")
        for ut in ctx['user_types']:
            lines.append(f"  - {ut['type']}: {ut['count']} người")
        lines.append("")

    if ctx.get('top_categories'):
        lines.append("🏆 **Top danh mục bán chạy:**")
        for tc in ctx['top_categories']:
            lines.append(f"  - {tc['category']}: {tc['purchases']} lượt mua")

    return "\n".join(lines)


def _format_general(ctx):
    return (
        "👋 **Xin chào! Tôi là AI Assistant của hệ thống E-commerce.**\n\n"
        "Tôi có thể giúp bạn:\n"
        "  🛒 **Gợi ý sản phẩm**: _\"Gợi ý sản phẩm cho user1\"_\n"
        "  👤 **Phân tích hành vi**: _\"Hành vi của user50\"_\n"
        "  🏆 **Sản phẩm phổ biến**: _\"Top sản phẩm bán chạy\"_\n"
        "  👥 **Người dùng tương tự**: _\"Tìm người tương tự user10\"_\n"
        "  📁 **Thống kê danh mục**: _\"Thống kê theo danh mục\"_\n"
        "  📈 **Phân tích funnel**: _\"Phân tích funnel chuyển đổi\"_\n"
        "  📊 **Tổng quan**: _\"Thống kê tổng quan\"_\n\n"
        "Hãy đặt câu hỏi để tôi truy vấn Knowledge Graph!"
    )


# ──────────────────────────────────────────────
# Main RAG Pipeline
# ──────────────────────────────────────────────

def rag_chat(question):
    """
    Main RAG pipeline: Question → Intent → Retrieve → Generate.

    Args:
        question: User's natural language question

    Returns:
        dict with keys: answer, intent, context_summary, cypher_used
    """
    try:
        driver = _get_neo4j_driver()
    except Exception as e:
        return {
            'answer': f"⚠️ Không thể kết nối Neo4j: {str(e)}",
            'intent': 'error',
            'context_summary': None,
        }

    # Step 1: Detect intent
    intent = detect_intent(question)
    user_ref = extract_user_ref(question)

    # Step 2: Retrieve from graph
    context = None
    error = None

    try:
        if intent == 'product_search':
            keyword = extract_product_keyword(question)
            context = retrieve_products_by_keyword(driver, keyword)
        elif intent == 'recommend':
            context, error = retrieve_recommendations(driver, user_ref)
        elif intent == 'user_info':
            context, error = retrieve_user_info(driver, user_ref)
        elif intent == 'product_info':
            context = retrieve_product_info(driver)
        elif intent == 'similar':
            context, error = retrieve_similar_users(driver, user_ref)
        elif intent == 'category':
            context = retrieve_category_stats(driver)
        elif intent == 'funnel':
            context = retrieve_funnel(driver)
        elif intent == 'stats':
            context = retrieve_stats(driver)
        else:
            context = retrieve_stats(driver)
    except Exception as e:
        logger.error(f"Graph retrieval error: {e}")
        error = f"Lỗi truy vấn graph: {str(e)}"
    finally:
        driver.close()

    # Step 3: Generate response
    if error:
        answer = f"⚠️ {error}"
    else:
        answer = generate_response(intent, context, question)

    return {
        'answer': answer,
        'intent': intent,
        'user_ref': user_ref,
    }
