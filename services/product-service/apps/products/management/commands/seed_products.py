import random
import re
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product


SEED_DATA = {
    'Điện thoại': {
        'description': 'Điện thoại thông minh mới nhất từ các thương hiệu hàng đầu',
        'icon': '📱',
        'products': [
            {
                'name': 'iPhone 16 Pro Max',
                'description': 'Apple iPhone 16 Pro Max với chip A18 Pro, màn hình Super Retina XDR 6.9 inch, hệ thống camera 48MP với zoom quang 5x, thiết kế titanium sang trọng.',
                'price': Decimal('1199.99'),
                'compare_price': Decimal('1299.99'),
                'stock': 50,
                'rating': Decimal('4.85'),
                'num_reviews': 2340,
                'image_url': '/images/products/iphone-16-pro-max.png',
            },
            {
                'name': 'Samsung Galaxy S25 Ultra',
                'description': 'Samsung Galaxy S25 Ultra trang bị Snapdragon 8 Elite, màn hình Dynamic AMOLED 2X 6.9 inch, camera 200MP, bút S Pen tích hợp, Galaxy AI thông minh.',
                'price': Decimal('1099.99'),
                'compare_price': Decimal('1199.99'),
                'stock': 35,
                'rating': Decimal('4.70'),
                'num_reviews': 1850,
                'image_url': '/images/products/samsung-galaxy-s25-ultra.jpg',
            },
        ],
    },
    'Laptop': {
        'description': 'Laptop mạnh mẽ cho công việc và giải trí',
        'icon': '💻',
        'products': [
            {
                'name': 'MacBook Pro 14" M4 Pro',
                'description': 'Apple MacBook Pro 14 inch với chip M4 Pro, 24GB bộ nhớ hợp nhất, SSD 1TB, màn hình Liquid Retina XDR, pin 17 giờ sử dụng.',
                'price': Decimal('1999.99'),
                'compare_price': Decimal('2199.99'),
                'stock': 20,
                'rating': Decimal('4.90'),
                'num_reviews': 980,
                'image_url': '/images/products/macbook-pro-14.png',
            },
            {
                'name': 'Dell XPS 15 OLED',
                'description': 'Dell XPS 15 với Intel Core Ultra 9, RAM 32GB, SSD 1TB, màn hình OLED 3.5K InfinityEdge 15.6 inch, card đồ họa NVIDIA RTX 4070.',
                'price': Decimal('1799.99'),
                'compare_price': Decimal('1999.99'),
                'stock': 15,
                'rating': Decimal('4.65'),
                'num_reviews': 720,
                'image_url': '/images/products/dell-xps-15.png',
            },
        ],
    },
    'Âm thanh': {
        'description': 'Tai nghe, loa và thiết bị âm thanh cao cấp',
        'icon': '🎧',
        'products': [
            {
                'name': 'Sony WH-1000XM6',
                'description': 'Tai nghe không dây chống ồn cao cấp Sony với công nghệ ANC hàng đầu thế giới, pin 40 giờ, LDAC Hi-Res Audio, kết nối đa điểm.',
                'price': Decimal('349.99'),
                'compare_price': Decimal('399.99'),
                'stock': 100,
                'rating': Decimal('4.75'),
                'num_reviews': 3200,
                'image_url': '/images/products/sony-wh1000xm6.png',
            },
            {
                'name': 'AirPods Pro 3',
                'description': 'Apple AirPods Pro 3 với chip H3, chống ồn chủ động thích ứng, âm thanh không gian, sạc USB-C, pin 6 giờ sử dụng liên tục.',
                'price': Decimal('249.99'),
                'compare_price': Decimal('279.99'),
                'stock': 200,
                'rating': Decimal('4.80'),
                'num_reviews': 5600,
                'image_url': '/images/products/airpods-pro-3.png',
            },
        ],
    },
    'Thời trang': {
        'description': 'Quần áo thời trang nam và nữ',
        'icon': '👕',
        'products': [
            {
                'name': 'Quần Jeans Levi\'s 501 Original',
                'description': 'Quần jeans Levi\'s 501 dáng thẳng kinh điển với khuy cài đặc trưng, ống thẳng, chất liệu denim cao cấp mang tính biểu tượng từ năm 1873.',
                'price': Decimal('69.99'),
                'compare_price': Decimal('89.99'),
                'stock': 300,
                'rating': Decimal('4.40'),
                'num_reviews': 8900,
                'image_url': '/images/products/quan-jeans-levi.jpg',
            },
            {
                'name': 'Áo Khoác Lông Vũ Uniqlo Ultra Light',
                'description': 'Áo khoác lông vũ siêu nhẹ Uniqlo. Cực kỳ ấm áp nhưng nhẹ tênh, chống nước, có thể gấp gọn vào túi đựng riêng để mang theo.',
                'price': Decimal('79.99'),
                'compare_price': Decimal('99.99'),
                'stock': 180,
                'rating': Decimal('4.55'),
                'num_reviews': 4200,
                'image_url': '/images/products/ao-khoac-long-vu-uniqlo-ultra-light.jpg',
            },
        ],
    },
    'Giày dép': {
        'description': 'Giày thể thao, boots và giày dép các loại',
        'icon': '👟',
        'products': [
            {
                'name': 'Nike Air Max 270 React',
                'description': 'Giày chạy bộ Nike Air Max 270 React kết hợp đệm Max Air và bọt React cho cảm giác êm ái, nhẹ nhàng khi di chuyển.',
                'price': Decimal('149.99'),
                'compare_price': Decimal('179.99'),
                'stock': 200,
                'rating': Decimal('4.50'),
                'num_reviews': 4500,
                'image_url': '/images/products/nike-air-max-270-react.jpg',
            },
            {
                'name': 'Adidas Ultraboost Light',
                'description': 'Adidas Ultraboost Light — đôi Ultraboost nhẹ nhất từ trước đến nay với đế giữa BOOST, đế ngoài cao su Continental, upper Primeknit+.',
                'price': Decimal('189.99'),
                'compare_price': Decimal('219.99'),
                'stock': 150,
                'rating': Decimal('4.65'),
                'num_reviews': 2100,
                'image_url': '/images/products/adidas-ultraboost-light.jpg',
            },
        ],
    },
    'Gia dụng': {
        'description': 'Thiết bị gia dụng thông minh cho ngôi nhà hiện đại',
        'icon': '🏠',
        'products': [
            {
                'name': 'Máy Hút Bụi Dyson V15 Detect',
                'description': 'Máy hút bụi không dây Dyson V15 Detect với tia laser phát hiện bụi, cảm biến áp điện, màn hình LCD, thời gian hoạt động lên đến 60 phút.',
                'price': Decimal('649.99'),
                'compare_price': Decimal('749.99'),
                'stock': 30,
                'rating': Decimal('4.80'),
                'num_reviews': 1560,
                'image_url': '/images/products/may-hut-bui-dyson-v15-detect.jpg',
            },
            {
                'name': 'Robot Hút Bụi iRobot Roomba j9+',
                'description': 'Robot hút bụi iRobot Roomba j9+ tự đổ rác với điều hướng PrecisionVision, làm sạch 3 giai đoạn và lập bản đồ thông minh.',
                'price': Decimal('599.99'),
                'compare_price': Decimal('799.99'),
                'stock': 25,
                'rating': Decimal('4.60'),
                'num_reviews': 2300,
                'image_url': '/images/products/robot-hut-bui-irobot-roomba-j9.jpg',
            },
        ],
    },
    'Nhà bếp': {
        'description': 'Dụng cụ nấu ăn, đồ bếp và phụ kiện nhà bếp',
        'icon': '🍳',
        'products': [
            {
                'name': 'Máy Trộn KitchenAid Artisan',
                'description': 'Máy trộn đứng KitchenAid Artisan dung tích 5 lít với 10 tốc độ, bát thép không gỉ, công nghệ trộn hành tinh chuyên nghiệp.',
                'price': Decimal('379.99'),
                'compare_price': Decimal('449.99'),
                'stock': 45,
                'rating': Decimal('4.85'),
                'num_reviews': 6700,
                'image_url': '/images/products/may-tron-kitchenaid-artisan.jpg',
            },
            {
                'name': 'Nồi Áp Suất Instant Pot Duo Plus',
                'description': 'Instant Pot 9 trong 1: nồi áp suất, nồi nấu chậm, nồi cơm điện, hấp, xào, làm sữa chua, hâm nóng, tiệt trùng — đa năng cho mọi bữa ăn.',
                'price': Decimal('89.99'),
                'compare_price': Decimal('119.99'),
                'stock': 250,
                'rating': Decimal('4.70'),
                'num_reviews': 12000,
                'image_url': '/images/products/noi-ap-suat-instant-pot-duo-plus.jpg',
            },
        ],
    },
    'Sách': {
        'description': 'Sách bán chạy và sách chuyên ngành',
        'icon': '📚',
        'products': [
            {
                'name': 'Clean Code - Robert C. Martin',
                'description': 'Cẩm nang phát triển phần mềm Agile. Học cách viết code sạch, dễ đọc và dễ bảo trì — cuốn sách không thể thiếu cho lập trình viên chuyên nghiệp.',
                'price': Decimal('39.99'),
                'compare_price': Decimal('49.99'),
                'stock': 500,
                'rating': Decimal('4.60'),
                'num_reviews': 15000,
                'image_url': '/images/products/clean-code---robert-c--martin.jpg',
            },
            {
                'name': 'System Design Interview - Alex Xu',
                'description': 'Hướng dẫn chuyên sâu về phỏng vấn thiết kế hệ thống của Alex Xu. Bao gồm khả năng mở rộng, hệ thống phân tán, microservices và kiến trúc thực tế.',
                'price': Decimal('34.99'),
                'compare_price': Decimal('44.99'),
                'stock': 400,
                'rating': Decimal('4.55'),
                'num_reviews': 8500,
                'image_url': '/images/products/system-design-interview---alex-xu.jpg',
            },
        ],
    },
    'Gaming': {
        'description': 'Máy chơi game, tay cầm và phụ kiện gaming',
        'icon': '🎮',
        'products': [
            {
                'name': 'PlayStation 5 Slim',
                'description': 'Sony PS5 Slim với SSD 1TB, tay cầm DualSense không dây, chơi game 4K ở 120fps, ray tracing, tương thích ngược với game PS4.',
                'price': Decimal('449.99'),
                'compare_price': Decimal('499.99'),
                'stock': 40,
                'rating': Decimal('4.80'),
                'num_reviews': 9800,
                'image_url': '/images/products/playstation-5-slim.jpg',
            },
            {
                'name': 'Nintendo Switch 2',
                'description': 'Nintendo Switch 2 với màn hình LCD 8 inch, tay cầm Joy-Con cải tiến, hỗ trợ công nghệ DLSS, tương thích ngược game Switch thế hệ trước.',
                'price': Decimal('399.99'),
                'compare_price': Decimal('449.99'),
                'stock': 60,
                'rating': Decimal('4.75'),
                'num_reviews': 3400,
                'image_url': '/images/products/nintendo-switch-2.jpg',
            },
        ],
    },
    'Đồng hồ': {
        'description': 'Đồng hồ thông minh và đồng hồ cao cấp',
        'icon': '⌚',
        'products': [
            {
                'name': 'Apple Watch Ultra 3',
                'description': 'Apple Watch Ultra 3 với vỏ titanium 49mm, GPS hai tần số chính xác cao, pin lên đến 72 giờ, máy tính lặn chuyên nghiệp, chip S10.',
                'price': Decimal('799.99'),
                'compare_price': Decimal('899.99'),
                'stock': 30,
                'rating': Decimal('4.85'),
                'num_reviews': 1200,
                'image_url': '/images/products/apple-watch-ultra-3.jpg',
            },
            {
                'name': 'Samsung Galaxy Watch 7',
                'description': 'Samsung Galaxy Watch 7 với cảm biến BioActive, đo thành phần cơ thể, theo dõi giấc ngủ chuyên sâu, Wear OS, pin 40 giờ sử dụng.',
                'price': Decimal('299.99'),
                'compare_price': Decimal('349.99'),
                'stock': 80,
                'rating': Decimal('4.50'),
                'num_reviews': 2800,
                'image_url': '/images/products/samsung-galaxy-watch-7.jpg',
            },
        ],
    },
    'Thể thao & Fitness': {
        'description': 'Dụng cụ thể thao, tập luyện và phụ kiện fitness',
        'icon': '🏋️',
        'products': [
            {
                'name': 'Xe Đạp Tập Peloton Bike+',
                'description': 'Xe đạp tập Peloton Bike+ với màn hình cảm ứng HD 24 inch xoay được, tự động điều chỉnh lực cản, tích hợp Apple GymKit và hệ thống loa.',
                'price': Decimal('2495.00'),
                'compare_price': Decimal('2795.00'),
                'stock': 10,
                'rating': Decimal('4.70'),
                'num_reviews': 3500,
                'image_url': '/images/products/xe-ap-tap-peloton-bike.jpg',
            },
            {
                'name': 'Súng Massage Theragun PRO Plus',
                'description': 'Therabody Theragun PRO Plus thiết bị trị liệu gõ rung với ứng dụng thông minh, 6 đầu massage chuyên dụng, công nghệ QuietForce siêu êm.',
                'price': Decimal('399.99'),
                'compare_price': Decimal('449.99'),
                'stock': 70,
                'rating': Decimal('4.65'),
                'num_reviews': 1800,
                'image_url': '/images/products/sung-massage-theragun-pro-plus.jpg',
            },
        ],
    },
    'Làm đẹp': {
        'description': 'Chăm sóc da, trang điểm và chăm sóc cá nhân',
        'icon': '💄',
        'products': [
            {
                'name': 'Máy Tạo Kiểu Tóc Dyson Airwrap',
                'description': 'Dyson Airwrap máy tạo kiểu tóc đa năng với công nghệ luồng khí Coanda. Uốn, tạo sóng, duỗi mượt và sấy khô mà không gây tổn thương nhiệt.',
                'price': Decimal('499.99'),
                'compare_price': Decimal('599.99'),
                'stock': 55,
                'rating': Decimal('4.75'),
                'num_reviews': 4100,
                'image_url': '/images/products/may-tao-kieu-toc-dyson-airwrap.jpg',
            },
            {
                'name': 'Kem Dưỡng Ẩm La Mer',
                'description': 'La Mer Kem Dưỡng Ẩm 60ml. Chứa Miracle Broth™ giúp cấp ẩm tối ưu, tái tạo da và tăng cường độ rạng rỡ tự nhiên cho làn da.',
                'price': Decimal('345.00'),
                'compare_price': Decimal('380.00'),
                'stock': 40,
                'rating': Decimal('4.80'),
                'num_reviews': 6200,
                'image_url': '/images/products/kem-duong-am-la-mer.jpg',
            },
        ],
    },
}

VND_PRICE_RANGES = {
    'Điện thoại': (Decimal('5000000'), Decimal('45000000')),
    'Laptop': (Decimal('12000000'), Decimal('80000000')),
    'Âm thanh': (Decimal('300000'), Decimal('25000000')),
    'Thời trang': (Decimal('150000'), Decimal('4000000')),
    'Giày dép': (Decimal('300000'), Decimal('7000000')),
    'Gia dụng': (Decimal('800000'), Decimal('50000000')),
    'Nhà bếp': (Decimal('100000'), Decimal('15000000')),
    'Sách': (Decimal('80000'), Decimal('700000')),
    'Gaming': (Decimal('500000'), Decimal('50000000')),
    'Đồng hồ': (Decimal('500000'), Decimal('45000000')),
    'Thể thao & Fitness': (Decimal('150000'), Decimal('60000000')),
    'Làm đẹp': (Decimal('90000'), Decimal('12000000')),
}

CATEGORY_IMAGES = {
    'Điện thoại': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&h=600&fit=crop&auto=format',
    'Laptop': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&h=600&fit=crop&auto=format',
    'Âm thanh': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=600&fit=crop&auto=format',
    'Thời trang': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800&h=600&fit=crop&auto=format',
    'Giày dép': 'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=800&h=600&fit=crop&auto=format',
    'Gia dụng': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&h=600&fit=crop&auto=format',
    'Nhà bếp': 'https://images.unsplash.com/photo-1556909114-44e3e70034e2?w=800&h=600&fit=crop&auto=format',
    'Sách': 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=800&h=600&fit=crop&auto=format',
    'Gaming': 'https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?w=800&h=600&fit=crop&auto=format',
    'Đồng hồ': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=800&h=600&fit=crop&auto=format',
    'Thể thao & Fitness': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&h=600&fit=crop&auto=format',
    'Làm đẹp': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800&h=600&fit=crop&auto=format',
}

USD_TO_VND_RATE = Decimal('26000')
THOUSAND = Decimal('1000')


def _round_to_thousand(value):
    rounded = (value / THOUSAND).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * THOUSAND
    return rounded.quantize(Decimal('0.01'))


def _slug_token(value):
    token = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return token or 'product'


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _price_to_vnd(category_name, usd_price, cycle, rng):
    min_price, max_price = VND_PRICE_RANGES[category_name]
    base_vnd = _to_decimal(usd_price) * USD_TO_VND_RATE
    variation = Decimal(str(rng.uniform(0.87, 1.18))) * Decimal(str(1 + ((cycle - 1) * 0.01)))
    adjusted = _round_to_thousand(base_vnd * variation)
    return _clamp(adjusted, min_price, max_price)


def _build_compare_price(price, category_name, rng):
    min_price, max_price = VND_PRICE_RANGES[category_name]
    markup = Decimal(str(rng.uniform(1.06, 1.28)))
    compare_price = _round_to_thousand(price * markup)
    compare_price = max(compare_price, price + THOUSAND)
    return _clamp(compare_price, min_price, max_price)


def _build_stock(base_stock, cycle, rng):
    scale = Decimal(str(rng.uniform(0.75, 1.45)))
    stock = int((Decimal(str(base_stock)) * scale) + (cycle - 1) * rng.randint(2, 6))
    return max(stock, 5)


def _build_rating(base_rating, rng):
    base = float(_to_decimal(base_rating))
    rating = max(3.70, min(4.99, base + rng.uniform(-0.18, 0.16)))
    return Decimal(f'{rating:.2f}')


def _build_reviews(base_reviews, cycle, rng):
    baseline = int(base_reviews * rng.uniform(0.28, 0.95))
    growth = rng.randint(80, 340) * cycle
    return max(20, baseline + growth)


def _build_slug(name, cycle):
    if cycle == 1:
        return slugify(name)
    return f'{slugify(name)}-phien-ban-{cycle}'


def _variant_name(template_name, cycle):
    if cycle == 1:
        return template_name
    return f'{template_name} Phiên Bản {cycle}'


def _variant_description(template_description, cycle):
    if cycle == 1:
        return (
            f'{template_description} Giá thị trường Việt Nam chính hãng, '
            'bảo hành toàn quốc, hỗ trợ giao hàng nhanh.'
        )
    return (
        f'{template_description} Phiên bản {cycle} thị trường Việt Nam với giá '
        'ưu đãi, bảo hành chính hãng, giao hàng toàn quốc nhanh chóng.'
    )


class Command(BaseCommand):
    help = 'Tạo dữ liệu sản phẩm với giá VND và hình ảnh sản phẩm (mặc định: 240 sản phẩm).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-category',
            type=int,
            default=2,
            help='Số lượng sản phẩm mỗi danh mục (mặc định: 2, tổng: 24).',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=2026,
            help='Seed cho bộ sinh số ngẫu nhiên.',
        )

    def handle(self, *args, **options):
        per_category = max(1, options['per_category'])
        rng = random.Random(options['seed'])
        target_total = per_category * len(SEED_DATA)

        self.stdout.write(
            f'Đang tạo danh mục sản phẩm với giá VND ({per_category} sản phẩm/danh mục, mục tiêu {target_total} sản phẩm)...'
        )

        created_count = 0
        updated_count = 0

        for category_index, (category_name, cat_data) in enumerate(SEED_DATA.items(), start=1):
            category_image = CATEGORY_IMAGES.get(category_name, '')
            category_defaults = {
                'description': cat_data['description'],
                'image_url': category_image,
            }
            category, category_created = Category.objects.get_or_create(
                name=category_name,
                defaults=category_defaults,
            )

            if not category_created:
                category_changed = False
                if category.description != cat_data['description']:
                    category.description = cat_data['description']
                    category_changed = True
                if category.image_url != category_image:
                    category.image_url = category_image
                    category_changed = True
                if category_changed:
                    category.save(update_fields=['description', 'image_url'])

            self.stdout.write(f'  Danh mục: {category_name}')

            templates = cat_data['products']
            for i in range(per_category):
                template = templates[i % len(templates)]
                cycle = (i // len(templates)) + 1

                name = _variant_name(template['name'], cycle)
                slug = _build_slug(template['name'], cycle)
                description = _variant_description(template['description'], cycle)

                price = _price_to_vnd(category_name, template['price'], cycle, rng)
                compare_price = _build_compare_price(price, category_name, rng)
                stock = _build_stock(template['stock'], cycle, rng)
                rating = _build_rating(template.get('rating', Decimal('4.20')), rng)
                num_reviews = _build_reviews(template.get('num_reviews', 120), cycle, rng)
                # Use the template's image URL directly for all variants
                image_url = template['image_url']

                product_defaults = {
                    'name': name,
                    'description': description,
                    'price': price,
                    'compare_price': compare_price,
                    'category': category,
                    'image_url': image_url,
                    'stock': stock,
                    'rating': rating,
                    'num_reviews': num_reviews,
                    'is_active': True,
                }

                product, created = Product.objects.get_or_create(slug=slug, defaults=product_defaults)
                if created:
                    created_count += 1
                    self.stdout.write(f'    + Đã tạo: {name}')
                    continue

                update_fields = []
                for field_name, expected_value in product_defaults.items():
                    if getattr(product, field_name) != expected_value:
                        setattr(product, field_name, expected_value)
                        update_fields.append(field_name)

                if update_fields:
                    product.save(update_fields=update_fields)
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Hoàn tất! Mục tiêu {target_total} sản phẩm, đã tạo {created_count}, cập nhật {updated_count}.'
            )
        )
