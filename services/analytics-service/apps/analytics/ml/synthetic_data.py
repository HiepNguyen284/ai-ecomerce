"""
Synthetic Data Generator for Customer Behavior Analysis.

Generates realistic synthetic behavioral data for training the deep learning
models. Creates diverse customer personas with varying purchase patterns:

- VIP / Champion customers: High frequency, high spending
- Loyal Regulars: Consistent medium spending
- Occasional Buyers: Sporadic purchases
- New Customers: Recent joins, few orders
- Churning Customers: Declining activity over time

Each customer generates view → add_to_cart → purchase event sequences
with realistic time distributions.
"""

import uuid
import random
import logging
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# Vietnamese product categories matching the e-commerce store
CATEGORIES = [
    'Điện thoại & Phụ kiện',
    'Laptop & Máy tính',
    'Thời trang Nam',
    'Thời trang Nữ',
    'Đồ gia dụng',
    'Sách & Văn phòng phẩm',
    'Thể thao & Du lịch',
    'Mẹ & Bé',
    'Sức khỏe & Làm đẹp',
    'Thực phẩm & Đồ uống',
    'Đồ chơi & Giải trí',
    'Ô tô & Xe máy',
]

# Products per category with price ranges
PRODUCTS_BY_CATEGORY = {
    'Điện thoại & Phụ kiện': [
        ('iPhone 15 Pro Max', 28000000, 35000000),
        ('Samsung Galaxy S24 Ultra', 25000000, 32000000),
        ('Ốp lưng điện thoại', 50000, 500000),
        ('Cáp sạc nhanh USB-C', 80000, 300000),
        ('Tai nghe Bluetooth', 200000, 3000000),
        ('Sạc dự phòng 20000mAh', 300000, 1000000),
    ],
    'Laptop & Máy tính': [
        ('MacBook Air M3', 25000000, 35000000),
        ('Laptop Gaming ASUS ROG', 20000000, 40000000),
        ('Bàn phím cơ', 500000, 3000000),
        ('Chuột không dây', 200000, 1500000),
        ('Màn hình 27 inch', 4000000, 15000000),
        ('Webcam HD', 300000, 2000000),
    ],
    'Thời trang Nam': [
        ('Áo thun nam basic', 150000, 500000),
        ('Quần jean nam slim', 300000, 800000),
        ('Giày sneaker nam', 500000, 3000000),
        ('Áo khoác nam', 400000, 1500000),
        ('Ví da nam', 200000, 1000000),
    ],
    'Thời trang Nữ': [
        ('Đầm dự tiệc', 300000, 1500000),
        ('Áo sơ mi nữ', 200000, 600000),
        ('Túi xách nữ', 300000, 5000000),
        ('Giày cao gót', 300000, 2000000),
        ('Phụ kiện thời trang', 50000, 500000),
    ],
    'Đồ gia dụng': [
        ('Nồi chiên không dầu', 1000000, 3000000),
        ('Máy hút bụi robot', 3000000, 15000000),
        ('Bộ nồi inox', 500000, 2000000),
        ('Máy lọc không khí', 2000000, 8000000),
        ('Bình giữ nhiệt', 150000, 500000),
    ],
    'Sách & Văn phòng phẩm': [
        ('Sách kinh doanh', 80000, 300000),
        ('Sách văn học', 60000, 200000),
        ('Bút bi cao cấp', 30000, 500000),
        ('Sổ tay ghi chép', 40000, 200000),
        ('Balo laptop', 300000, 1500000),
    ],
    'Thể thao & Du lịch': [
        ('Giày chạy bộ', 500000, 3000000),
        ('Bộ quần áo thể thao', 200000, 800000),
        ('Vali du lịch', 500000, 3000000),
        ('Đồng hồ thể thao', 500000, 5000000),
        ('Bình nước thể thao', 100000, 300000),
    ],
    'Mẹ & Bé': [
        ('Sữa bột trẻ em', 300000, 800000),
        ('Tã giấy', 200000, 500000),
        ('Xe đẩy em bé', 2000000, 8000000),
        ('Đồ chơi giáo dục', 100000, 500000),
        ('Quần áo trẻ em', 100000, 400000),
    ],
    'Sức khỏe & Làm đẹp': [
        ('Kem chống nắng', 150000, 500000),
        ('Serum dưỡng da', 200000, 1000000),
        ('Máy massage cầm tay', 300000, 2000000),
        ('Vitamin tổng hợp', 200000, 800000),
        ('Nước hoa', 500000, 5000000),
    ],
    'Thực phẩm & Đồ uống': [
        ('Cà phê hạt nguyên chất', 100000, 500000),
        ('Trà Oolong cao cấp', 150000, 600000),
        ('Hạt dinh dưỡng mix', 100000, 300000),
        ('Mật ong nguyên chất', 150000, 400000),
        ('Socola Bỉ', 100000, 500000),
    ],
    'Đồ chơi & Giải trí': [
        ('LEGO Creator', 500000, 3000000),
        ('Board game', 200000, 800000),
        ('Mô hình lắp ráp', 300000, 1500000),
        ('Rubik cube', 50000, 300000),
        ('Máy chơi game cầm tay', 2000000, 8000000),
    ],
    'Ô tô & Xe máy': [
        ('Mũ bảo hiểm fullface', 500000, 3000000),
        ('Găng tay lái xe', 100000, 500000),
        ('Camera hành trình', 500000, 3000000),
        ('Nước hoa ô tô', 100000, 500000),
        ('Phụ kiện xe máy', 50000, 2000000),
    ],
}


class CustomerPersona:
    """Defines a customer persona with purchasing behavior parameters."""

    def __init__(self, name, order_count_range, avg_spent_range,
                 order_interval_range, preferred_categories,
                 churn_probability, cancel_ratio, active_months):
        self.name = name
        self.order_count_range = order_count_range
        self.avg_spent_range = avg_spent_range
        self.order_interval_range = order_interval_range
        self.preferred_categories = preferred_categories
        self.churn_probability = churn_probability
        self.cancel_ratio = cancel_ratio
        self.active_months = active_months


# Define customer personas
PERSONAS = [
    CustomerPersona(
        name='VIP Champion',
        order_count_range=(20, 50),
        avg_spent_range=(2000000, 15000000),
        order_interval_range=(2, 10),
        preferred_categories=random.sample(CATEGORIES, 4),
        churn_probability=0.05,
        cancel_ratio=0.02,
        active_months=12,
    ),
    CustomerPersona(
        name='Loyal Regular',
        order_count_range=(10, 25),
        avg_spent_range=(500000, 3000000),
        order_interval_range=(5, 20),
        preferred_categories=random.sample(CATEGORIES, 3),
        churn_probability=0.1,
        cancel_ratio=0.05,
        active_months=9,
    ),
    CustomerPersona(
        name='Occasional Buyer',
        order_count_range=(3, 10),
        avg_spent_range=(200000, 1500000),
        order_interval_range=(15, 45),
        preferred_categories=random.sample(CATEGORIES, 2),
        churn_probability=0.3,
        cancel_ratio=0.08,
        active_months=6,
    ),
    CustomerPersona(
        name='New Customer',
        order_count_range=(1, 5),
        avg_spent_range=(100000, 800000),
        order_interval_range=(3, 15),
        preferred_categories=random.sample(CATEGORIES, 2),
        churn_probability=0.4,
        cancel_ratio=0.1,
        active_months=2,
    ),
    CustomerPersona(
        name='Churning Customer',
        order_count_range=(5, 15),
        avg_spent_range=(200000, 2000000),
        order_interval_range=(7, 30),
        preferred_categories=random.sample(CATEGORIES, 3),
        churn_probability=0.8,
        cancel_ratio=0.15,
        active_months=8,
    ),
]


def generate_synthetic_data(num_customers=500, seed=42):
    """
    Generate synthetic customer behavior data.

    Args:
        num_customers: number of synthetic customers to generate
        seed: random seed for reproducibility

    Returns:
        dict with keys:
            - events_by_customer: dict mapping customer_id → list of events
            - customer_metadata: dict mapping customer_id → metadata dict
            - category_to_idx: dict mapping category → index
    """
    random.seed(seed)
    np.random.seed(seed)

    events_by_customer = {}
    customer_metadata = {}
    now = timezone.now()

    # Persona distribution weights
    persona_weights = [0.08, 0.25, 0.30, 0.20, 0.17]

    category_to_idx = {cat: idx + 1 for idx, cat in enumerate(CATEGORIES)}

    for i in range(num_customers):
        customer_id = str(uuid.uuid4())
        persona = random.choices(PERSONAS, weights=persona_weights, k=1)[0]

        # Randomize persona slightly for this customer
        preferred_cats = random.sample(
            CATEGORIES,
            min(random.randint(1, 5), len(CATEGORIES))
        )
        # Weight preferred categories from persona
        cat_weights = []
        for cat in CATEGORIES:
            if cat in persona.preferred_categories:
                cat_weights.append(3.0)
            elif cat in preferred_cats:
                cat_weights.append(1.5)
            else:
                cat_weights.append(0.5)

        num_orders = random.randint(*persona.order_count_range)
        active_start = now - timedelta(days=persona.active_months * 30)

        events = []
        current_time = active_start + timedelta(
            days=random.randint(0, 14))

        # Generate purchase hour preferences
        preferred_hours = _generate_hour_preferences()
        preferred_days = _generate_day_preferences()

        for order_idx in range(num_orders):
            # Pick category
            cat = random.choices(CATEGORIES, weights=cat_weights, k=1)[0]
            products = PRODUCTS_BY_CATEGORY.get(cat, [])
            if not products:
                continue

            product = random.choice(products)
            product_name, price_min, price_max = product
            price = random.randint(price_min, price_max)
            quantity = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
            product_id = str(uuid.uuid4())

            # Adjust time to preferred hours/days
            hour = random.choices(
                range(24), weights=preferred_hours, k=1)[0]
            current_time = current_time.replace(
                hour=hour,
                minute=random.randint(0, 59),
            )

            # View event (1-5 views before purchase)
            num_views = random.randint(1, 5)
            view_time = current_time - timedelta(
                hours=random.randint(1, 48))
            for _ in range(num_views):
                events.append({
                    'event_type': 'view',
                    'product_id': product_id,
                    'product_name': product_name,
                    'category_name': cat,
                    'amount': 0,
                    'quantity': 0,
                    'timestamp': view_time,
                    'metadata': {},
                })
                view_time += timedelta(minutes=random.randint(5, 120))

            # Add to cart event
            cart_time = current_time - timedelta(
                minutes=random.randint(10, 300))
            events.append({
                'event_type': 'add_to_cart',
                'product_id': product_id,
                'product_name': product_name,
                'category_name': cat,
                'amount': price,
                'quantity': quantity,
                'timestamp': cart_time,
                'metadata': {},
            })

            # Purchase or cancel
            is_cancelled = random.random() < persona.cancel_ratio
            if is_cancelled:
                events.append({
                    'event_type': 'cancel',
                    'product_id': product_id,
                    'product_name': product_name,
                    'category_name': cat,
                    'amount': price * quantity,
                    'quantity': quantity,
                    'timestamp': current_time + timedelta(
                        hours=random.randint(1, 24)),
                    'metadata': {'reason': random.choice([
                        'Đổi ý', 'Tìm được giá rẻ hơn',
                        'Hết tiền', 'Đặt nhầm',
                    ])},
                })
            else:
                events.append({
                    'event_type': 'purchase',
                    'product_id': product_id,
                    'product_name': product_name,
                    'category_name': cat,
                    'amount': price * quantity,
                    'quantity': quantity,
                    'timestamp': current_time,
                    'metadata': {},
                })

            # Advance time
            interval = random.randint(*persona.order_interval_range)
            # For churning customers, increase interval over time
            if persona.name == 'Churning Customer':
                interval = int(interval * (1 + order_idx * 0.3))

            current_time += timedelta(days=interval)
            if current_time > now:
                break

        # Add some random search events
        for _ in range(random.randint(2, 15)):
            search_time = active_start + timedelta(
                days=random.randint(0, persona.active_months * 30))
            if search_time > now:
                continue
            events.append({
                'event_type': 'search',
                'product_id': None,
                'product_name': '',
                'category_name': random.choice(CATEGORIES),
                'amount': 0,
                'quantity': 0,
                'timestamp': search_time,
                'metadata': {'query': random.choice([
                    'điện thoại giá rẻ', 'laptop gaming', 'áo thun nam',
                    'quà tặng sinh nhật', 'giảm giá', 'kem chống nắng',
                    'sách hay', 'đồ chơi trẻ em',
                ])},
            })

        events.sort(key=lambda e: e['timestamp'])
        events_by_customer[customer_id] = events

        customer_metadata[customer_id] = {
            'persona': persona.name,
            'email': f'customer_{i+1}@example.com',
            'name': f'Khách hàng {i+1}',
            'preferred_categories': preferred_cats[:3],
            'is_churned': random.random() < persona.churn_probability,
        }

    logger.info(f"Generated {num_customers} synthetic customers "
                f"with {sum(len(e) for e in events_by_customer.values())} events")

    return {
        'events_by_customer': events_by_customer,
        'customer_metadata': customer_metadata,
        'category_to_idx': category_to_idx,
    }


def _generate_hour_preferences():
    """Generate hour preference weights (peak at lunch and evening)."""
    weights = np.zeros(24)
    # Morning: 7-9
    weights[7:10] = [1.0, 1.5, 1.0]
    # Lunch: 11-13
    weights[11:14] = [2.0, 3.0, 2.0]
    # Afternoon: 14-17
    weights[14:18] = [1.5, 1.5, 1.0, 0.8]
    # Evening peak: 19-22
    weights[19:23] = [3.0, 4.0, 3.5, 2.0]
    # Add some noise
    weights += 0.1
    return weights.tolist()


def _generate_day_preferences():
    """Generate day-of-week preference weights."""
    # Mon=0 ... Sun=6; higher on weekends
    return [1.0, 1.0, 1.2, 1.2, 1.5, 2.5, 2.0]
