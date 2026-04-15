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

# Clear existing products and categories
print("Clearing existing products and categories...")
Product.objects.all().delete()
Category.objects.all().delete()

# Predefined categories and related image keywords
CATEGORIES = {
    'Laptop': ['laptop', 'macbook', 'computer', 'ultrabook', 'gaming laptop'],
    'Điện thoại': ['smartphone', 'iphone', 'phone', 'mobile', 'cellphone'],
    'Tai nghe': ['headphone', 'earbuds', 'airpods', 'audio', 'headset'],
    'Đồng hồ thông minh': ['smartwatch', 'apple watch', 'watch', 'wearable', 'fitness tracker'],
    'Máy tính bảng': ['tablet', 'ipad', 'galaxy tab', 'screen', 'device'],
    'Phụ kiện': ['charger', 'cable', 'mouse', 'keyboard', 'powerbank'],
    'Camera': ['camera', 'lens', 'photography', 'dslr', 'mirrorless'],
    'Màn hình': ['monitor', 'screen', 'display', '4k monitor', 'gaming monitor'],
}

BRANDS = {
    'Laptop': ['Apple', 'Dell', 'Asus', 'HP', 'Lenovo', 'Acer', 'MSI', 'Gigabyte'],
    'Điện thoại': ['Apple', 'Samsung', 'Xiaomi', 'Oppo', 'Vivo', 'Google', 'OnePlus'],
    'Tai nghe': ['Sony', 'Apple', 'JBL', 'Bose', 'Sennheiser', 'Marshall', 'Beats'],
    'Đồng hồ thông minh': ['Apple', 'Samsung', 'Garmin', 'Amazfit', 'Huawei', 'Fitbit'],
    'Máy tính bảng': ['Apple', 'Samsung', 'Xiaomi', 'Lenovo', 'Microsoft'],
    'Phụ kiện': ['Anker', 'Baseus', 'Logitech', 'Ugreen', 'Belkin', 'Razer'],
    'Camera': ['Sony', 'Canon', 'Nikon', 'Fujifilm', 'Panasonic', 'GoPro'],
    'Màn hình': ['LG', 'Samsung', 'Dell', 'ASUS', 'AOC', 'ViewSonic', 'BenQ']
}

DESCRIPTIONS = [
    "Sản phẩm công nghệ tiên tiến với thiết kế hiện đại, mang lại trải nghiệm tuyệt vời cho người dùng. Hiệu năng vượt trội giúp hoàn thành mọi công việc một cách nhanh chóng và dễ dàng. Phù hợp cho cả nhu cầu giải trí lẫn công việc chuyên nghiệp.",
    "Trang bị công nghệ mới nhất, sản phẩm này đảm bảo hiệu suất mạnh mẽ và độ bền cao. Thiết kế mỏng nhẹ, tinh tế giúp dễ dàng mang theo mọi nơi. Dung lượng pin lớn, đáp ứng nhu cầu sử dụng suốt cả ngày dài một cách hoàn hảo.",
    "Khả năng xử lý đồ họa mượt mà, bộ nhớ lưu trữ lớn, giúp bạn thoải mái lưu trữ dữ liệu và tận hưởng các ứng dụng mượt mà không độ trễ. Thiết kế sang trọng, màu sắc thời thượng phù hợp với mọi phong cách cá nhân.",
    "Mang đến chất lượng hình ảnh và âm thanh sống động, hệ thống tản nhiệt tiên tiến giúp máy luôn vận hành êm ái và không bị nóng. Màn hình sắc nét, độ tương phản cao, tối ưu cho việc xem phim, chơi game hay chỉnh sửa ảnh.",
    "Giao diện trực quan, thân thiện với người dùng. Cấu hình mạnh mẽ kết hợp cùng các tính năng thông minh giúp tối đa hóa hiệu suất làm việc. Ngoài ra, khả năng bảo mật được nâng cao bảo vệ dữ liệu cá nhân của bạn."
]

print("Creating categories...")
category_objects = {}
for cat_name in CATEGORIES.keys():
    cat = Category.objects.create(
        name=cat_name,
        description=f"Danh mục sản phẩm {cat_name} cao cấp.",
        image_url=f"https://loremflickr.com/800/600/{CATEGORIES[cat_name][0]}"
    )
    category_objects[cat_name] = cat

print("Generating 100 products...")
products_created = 0

while products_created < 100:
    for cat_name, keywords in CATEGORIES.items():
        if products_created >= 100:
            break
            
        brand = random.choice(BRANDS[cat_name])
        model_num = f"{random.randint(1, 99)}{random.choice(['Pro', 'Max', 'Ultra', 'Plus', 'Air', 'Lite', 'Mini', ''])}"
        
        product_name = f"{cat_name} {brand} {model_num} {random.randint(128, 1024)}GB"
        if cat_name in ['Phụ kiện', 'Tai nghe', 'Đồng hồ thông minh']:
            product_name = f"{cat_name} {brand} {model_num} Thế hệ {random.randint(1, 6)}"
        elif cat_name == 'Màn hình':
            product_name = f"{cat_name} {brand} {model_num} {random.choice([24, 27, 32])} inch 4K"
            
        slug = f"{slugify(product_name)}-{random.randint(1000, 9999)}"
        
        # Base price matching categories realistically (rough approx in VND)
        if cat_name == 'Laptop':
            price = random.randint(15, 60) * 1000000
        elif cat_name == 'Điện thoại':
            price = random.randint(8, 35) * 1000000
        elif cat_name == 'Phụ kiện':
            price = random.randint(3, 20) * 100000
        elif cat_name == 'Tai nghe':
            price = random.randint(1, 15) * 1000000
        else:
            price = random.randint(5, 30) * 1000000
            
        has_discount = random.random() > 0.6
        compare_price = price + (price * Decimal(random.randint(1, 20)/100)) if has_discount else None
        
        desc = f"**{product_name}** - {random.choice(DESCRIPTIONS)} Khám phá thế giới công nghệ cùng thương hiệu {brand} hàng đầu."
        
        # Use specific keywords dynamically with random seed to guarantee distinct images
        keyword = random.choice(keywords)
        image_url = f"https://loremflickr.com/800/600/{keyword}?lock={random.randint(1, 10000)}"
        
        Product.objects.create(
            name=product_name,
            slug=slug,
            description=desc,
            price=price,
            compare_price=compare_price,
            category=category_objects[cat_name],
            image_url=image_url,
            stock=random.randint(0, 100),
            rating=Decimal(random.uniform(3.5, 5.0)).quantize(Decimal('0.01')),
            num_reviews=random.randint(5, 150),
            is_active=True
        )
        products_created += 1

print(f"Successfully created {products_created} products with realistic data and varied image links!")
