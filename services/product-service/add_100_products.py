import os
import sys
import django
import random
from decimal import Decimal
from django.utils.text import slugify

# Add proper paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_service.settings')
django.setup()

from apps.products.models import Category, Product

# Categories to image keywords mapping corresponding to existing seeded categories
CATEGORIES_MAP = {
    'Quần': ['pants', 'jeans', 'trousers', 'shorts', 'chinos'],
    'Áo': ['shirt', 'tshirt', 'hoodie', 'jacket', 'blouse'],
    'Giầy': ['shoes', 'sneakers', 'boots', 'sandals', 'running shoes'],
    'Laptop': ['laptop', 'macbook', 'ultrabook', 'computer', 'notebook'],
    'Điện thoại': ['smartphone', 'iphone', 'mobile', 'cellphone', 'android'],
    'Đồng hồ': ['watch', 'smartwatch', 'rolex', 'apple watch', 'timepiece'],
    'Ô tô': ['car accessories', 'dashcam', 'car charger', 'auto', 'car mount'],
    'Sách': ['book', 'novel', 'reading', 'programming book', 'literature'],
    'Mỹ phẩm': ['cosmetics', 'skincare', 'makeup', 'serum', 'perfume'],
    'Âm thanh': ['headphones', 'speaker', 'earbuds', 'audio', 'sound system'],
    'Đồ gia dụng': ['appliances', 'vacuum', 'blender', 'air fryer', 'kitchen'],
    'Túi xách': ['bag', 'backpack', 'handbag', 'wallet', 'purse']
}

BRANDS = {
    'Quần': ['Levi\'s', 'Zara', 'Uniqlo', 'H&M', 'Coolmate', 'Yody'],
    'Áo': ['Nike', 'Adidas', 'Puma', 'Gucci', 'Tommy Hilfiger', 'Ralph Lauren'],
    'Giầy': ['Nike', 'Adidas', 'Vans', 'Converse', 'New Balance', 'Puma', 'Skechers'],
    'Laptop': ['Apple', 'Dell', 'HP', 'Lenovo', 'Asus', 'MSI', 'Acer'],
    'Điện thoại': ['Apple', 'Samsung', 'Xiaomi', 'Oppo', 'Pixel', 'Sony'],
    'Đồng hồ': ['Casio', 'Seiko', 'Apple', 'Samsung', 'Garmin', 'Citizen'],
    'Ô tô': ['Michelin', 'Xiaomi', 'Baseus', 'Anker', 'Vietmap'],
    'Sách': ['NXB Trẻ', 'Nhã Nam', 'O\'Reilly', 'Wiley', 'Penguin'],
    'Mỹ phẩm': ['L\'Oreal', 'Estée Lauder', 'MAC', 'Innisfree', 'Laneige', 'Kiehl\'s'],
    'Âm thanh': ['Sony', 'Bose', 'Marshall', 'JBL', 'Sennheiser', 'Bang & Olufsen'],
    'Đồ gia dụng': ['Philips', 'Panasonic', 'Xiaomi', 'Electrolux', 'Dyson', 'Sharp'],
    'Túi xách': ['Louis Vuitton', 'Coach', 'Tomtoc', 'Herschel', 'Samsonite', 'Aldo']
}

DESCRIPTIONS = [
    "Sản phẩm chất lượng cao với thiết kế hiện đại, bền bỉ và vô cùng nổi bật trong phân khúc. Mang lại sự tự tin và trải nghiệm hoàn hảo cho mọi nhu cầu hằng ngày.",
    "Mang phong cách vượt thời gian, thiết kế tinh gọn nhưng lại vô cùng cuốn hút. Sản phẩm giúp bạn dễ dàng kết nối cuộc sống hiện đại một cách tiện nghi nhất.",
    "Công nghệ hàng đầu được tích hợp trong sản phẩm nhỏ gọn. Từ vật liệu cao cấp đến mức độ hoàn thiện tỉ mỉ, đây là lựa chọn đáng giá để bạn thể hiện đẳng cấp.",
    "Đáp ứng xuất sắc cả nhu cầu công việc lẫn giải trí. Màu sắc nhã nhặn, chất liệu an toàn, thiết kế tối ưu hóa trải nghiệm người dùng đến từng chi tiết nhỏ.",
    "Được các chuyên gia và hàng ngàn khách hàng tin dùng. Hãy để sản phẩm này trở thành người bạn đồng hành không thể thiếu của bạn mỗi ngày."
]

def generate_products():
    categories = Category.objects.all()
    if not categories.exists():
        print("Không tìm thấy Category nào. Hãy tải lại dữ liệu seed gốc trước.")
        return

    cat_map = {c.name: c for c in categories}
    
    print("Generating 100 new products...")
    
    for i in range(100):
        # Pick random category
        cat_name = random.choice(list(CATEGORIES_MAP.keys()))
        category = cat_map.get(cat_name)
        if not category:
            continue
            
        brand = random.choice(BRANDS[cat_name])
        model_num = f"Pro {random.randint(1, 99)}"
        
        # Product name
        product_name = f"{cat_name} {brand} {model_num} Thế Hệ Mới"
        if cat_name in ['Laptop', 'Điện thoại']:
            product_name = f"{cat_name} {brand} {random.choice(['Ultra', 'Max', 'Lite'])} {random.choice([128, 256, 512])}GB"
        elif cat_name == 'Sách':
            product_name = f'Sách "{random.choice(["Lập Trình", "Tâm Lý", "Kinh Doanh", "Sức Khỏe"])} {random.randint(101, 999)}" - {brand}'
            
        # Guarantee a unique slug
        slug = f"{slugify(product_name)}-v{random.randint(10000, 99999)}"
        
        # Determine price based on category
        if cat_name in ['Laptop']:
            price = random.randint(15, 60) * 1000000
        elif cat_name in ['Điện thoại']:
            price = random.randint(5, 35) * 1000000
        elif cat_name in ['Giầy', 'Áo', 'Quần', 'Túi xách', 'Đồ gia dụng', 'Âm thanh']:
            price = random.randint(5, 50) * 100000
        elif cat_name == 'Sách':
            price = random.randint(1, 5) * 50000
        else:
            price = random.randint(2, 20) * 100000
            
        has_discount = random.random() > 0.5
        compare_price = price + (price * Decimal(random.randint(10, 40) / 100)) if has_discount else None
        
        # Image
        keyword = random.choice(CATEGORIES_MAP[cat_name])
        image_url = f"https://loremflickr.com/600/600/{keyword}?lock={random.randint(1, 5000)}"
        
        desc = f"**{product_name}** - {random.choice(DESCRIPTIONS)} Khám phá thiết kế dẫn đầu xu hướng cùng với sự đảm bảo uy tín từ thương hiệu lớn."
        
        Product.objects.create(
            name=product_name,
            slug=slug,
            description=desc,
            price=price,
            compare_price=compare_price,
            category=category,
            image_url=image_url,
            stock=random.randint(10, 200),
            rating=Decimal(random.uniform(4.0, 5.0)).quantize(Decimal('0.01')),
            num_reviews=random.randint(10, 500),
            is_active=True
        )

    count = Product.objects.count()
    print(f"Hoàn tất tạo thêm 100 sản phẩm. Hiện có tổng cộng {count} sản phẩm trong database!")

if __name__ == "__main__":
    generate_products()