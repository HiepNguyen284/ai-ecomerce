import random
import re
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product


SEED_DATA = {
    'Smartphones': {
        'description': 'Latest smartphones from top brands',
        'icon': '📱',
        'products': [
            {
                'name': 'iPhone 16 Pro Max',
                'description': 'Apple iPhone 16 Pro Max with A18 Pro chip, 6.9-inch Super Retina XDR display, 48MP camera system with 5x optical zoom, titanium design.',
                'price': Decimal('1199.99'),
                'compare_price': Decimal('1299.99'),
                'stock': 50,
                'rating': Decimal('4.85'),
                'num_reviews': 2340,
                'image_url': 'https://placehold.co/600x600/6c63ff/fff?text=iPhone+16+Pro',
            },
            {
                'name': 'Samsung Galaxy S25 Ultra',
                'description': 'Samsung Galaxy S25 Ultra featuring Snapdragon 8 Elite, 6.9-inch Dynamic AMOLED 2X, 200MP camera, built-in S Pen, Galaxy AI.',
                'price': Decimal('1099.99'),
                'compare_price': Decimal('1199.99'),
                'stock': 35,
                'rating': Decimal('4.70'),
                'num_reviews': 1850,
                'image_url': 'https://placehold.co/600x600/16213e/fff?text=Galaxy+S25',
            },
        ],
    },
    'Laptops': {
        'description': 'Powerful laptops for work and play',
        'icon': '💻',
        'products': [
            {
                'name': 'MacBook Pro 14" M4 Pro',
                'description': 'Apple MacBook Pro 14-inch with M4 Pro chip, 24GB unified memory, 1TB SSD, Liquid Retina XDR display, 17h battery.',
                'price': Decimal('1999.99'),
                'compare_price': Decimal('2199.99'),
                'stock': 20,
                'rating': Decimal('4.90'),
                'num_reviews': 980,
                'image_url': 'https://placehold.co/600x600/0f3460/fff?text=MacBook+Pro',
            },
            {
                'name': 'Dell XPS 15 OLED',
                'description': 'Dell XPS 15 with Intel Core Ultra 9, 32GB RAM, 1TB SSD, 15.6-inch 3.5K OLED InfinityEdge display, NVIDIA RTX 4070.',
                'price': Decimal('1799.99'),
                'compare_price': Decimal('1999.99'),
                'stock': 15,
                'rating': Decimal('4.65'),
                'num_reviews': 720,
                'image_url': 'https://placehold.co/600x600/1a1a2e/fff?text=Dell+XPS+15',
            },
        ],
    },
    'Audio': {
        'description': 'Headphones, speakers & audio gear',
        'icon': '🎧',
        'products': [
            {
                'name': 'Sony WH-1000XM6',
                'description': 'Sony premium wireless noise-cancelling headphones with industry-leading ANC, 40-hour battery, LDAC Hi-Res Audio, multipoint.',
                'price': Decimal('349.99'),
                'compare_price': Decimal('399.99'),
                'stock': 100,
                'rating': Decimal('4.75'),
                'num_reviews': 3200,
                'image_url': 'https://placehold.co/600x600/533483/fff?text=Sony+XM6',
            },
            {
                'name': 'AirPods Pro 3',
                'description': 'Apple AirPods Pro 3 with H3 chip, adaptive noise cancellation, spatial audio, USB-C charging, 6-hour battery life.',
                'price': Decimal('249.99'),
                'compare_price': Decimal('279.99'),
                'stock': 200,
                'rating': Decimal('4.80'),
                'num_reviews': 5600,
                'image_url': 'https://placehold.co/600x600/e94560/fff?text=AirPods+Pro',
            },
        ],
    },
    'Clothing': {
        'description': 'Fashion clothing for men & women',
        'icon': '👕',
        'products': [
            {
                'name': 'Levi\'s 501 Original Jeans',
                'description': 'The iconic Levi\'s 501 Original Fit jeans with signature button fly, straight leg, and premium denim since 1873.',
                'price': Decimal('69.99'),
                'compare_price': Decimal('89.99'),
                'stock': 300,
                'rating': Decimal('4.40'),
                'num_reviews': 8900,
                'image_url': 'https://placehold.co/600x600/1a1a2e/fff?text=Levi+501',
            },
            {
                'name': 'Uniqlo Ultra Light Down Jacket',
                'description': 'Uniqlo ultra-light premium down jacket. Incredibly warm yet lightweight, water-repellent, and packs into its own pouch.',
                'price': Decimal('79.99'),
                'compare_price': Decimal('99.99'),
                'stock': 180,
                'rating': Decimal('4.55'),
                'num_reviews': 4200,
                'image_url': 'https://placehold.co/600x600/0f3460/fff?text=Uniqlo+Down',
            },
        ],
    },
    'Shoes': {
        'description': 'Sneakers, boots & footwear',
        'icon': '👟',
        'products': [
            {
                'name': 'Nike Air Max 270 React',
                'description': 'Nike Air Max 270 React running shoes combining Max Air and React foam for a super-smooth, lightweight ride.',
                'price': Decimal('149.99'),
                'compare_price': Decimal('179.99'),
                'stock': 200,
                'rating': Decimal('4.50'),
                'num_reviews': 4500,
                'image_url': 'https://placehold.co/600x600/e94560/fff?text=Nike+Air+Max',
            },
            {
                'name': 'Adidas Ultraboost Light',
                'description': 'Adidas Ultraboost Light — the lightest Ultraboost ever with BOOST midsole, Continental rubber outsole, Primeknit+ upper.',
                'price': Decimal('189.99'),
                'compare_price': Decimal('219.99'),
                'stock': 150,
                'rating': Decimal('4.65'),
                'num_reviews': 2100,
                'image_url': 'https://placehold.co/600x600/533483/fff?text=Ultraboost',
            },
        ],
    },
    'Home Appliances': {
        'description': 'Smart home & kitchen appliances',
        'icon': '🏠',
        'products': [
            {
                'name': 'Dyson V15 Detect Vacuum',
                'description': 'Dyson V15 Detect cordless vacuum with laser dust detection, piezo sensor, LCD screen, up to 60 minutes runtime.',
                'price': Decimal('649.99'),
                'compare_price': Decimal('749.99'),
                'stock': 30,
                'rating': Decimal('4.80'),
                'num_reviews': 1560,
                'image_url': 'https://placehold.co/600x600/16213e/fff?text=Dyson+V15',
            },
            {
                'name': 'iRobot Roomba j9+',
                'description': 'iRobot Roomba j9+ self-emptying robot vacuum with PrecisionVision navigation, 3-stage cleaning, and smart mapping.',
                'price': Decimal('599.99'),
                'compare_price': Decimal('799.99'),
                'stock': 25,
                'rating': Decimal('4.60'),
                'num_reviews': 2300,
                'image_url': 'https://placehold.co/600x600/6c63ff/fff?text=Roomba+j9',
            },
        ],
    },
    'Kitchen': {
        'description': 'Cookware, utensils & kitchen tools',
        'icon': '🍳',
        'products': [
            {
                'name': 'KitchenAid Artisan Mixer',
                'description': 'KitchenAid Artisan 5-Quart tilt-head stand mixer with 10 speeds, stainless steel bowl, planetary mixing action.',
                'price': Decimal('379.99'),
                'compare_price': Decimal('449.99'),
                'stock': 45,
                'rating': Decimal('4.85'),
                'num_reviews': 6700,
                'image_url': 'https://placehold.co/600x600/e94560/fff?text=KitchenAid',
            },
            {
                'name': 'Instant Pot Duo Plus',
                'description': 'Instant Pot 9-in-1: pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker, warmer, sterilizer.',
                'price': Decimal('89.99'),
                'compare_price': Decimal('119.99'),
                'stock': 250,
                'rating': Decimal('4.70'),
                'num_reviews': 12000,
                'image_url': 'https://placehold.co/600x600/1a1a2e/fff?text=Instant+Pot',
            },
        ],
    },
    'Books': {
        'description': 'Bestselling books & textbooks',
        'icon': '📚',
        'products': [
            {
                'name': 'Clean Code - Robert C. Martin',
                'description': 'A handbook of agile software craftsmanship. Learn to write code that is clean, readable, and maintainable.',
                'price': Decimal('39.99'),
                'compare_price': Decimal('49.99'),
                'stock': 500,
                'rating': Decimal('4.60'),
                'num_reviews': 15000,
                'image_url': 'https://placehold.co/600x600/0f3460/fff?text=Clean+Code',
            },
            {
                'name': 'System Design Interview',
                'description': 'An insider\'s guide by Alex Xu. Covers scalability, distributed systems, microservices, and real-world architecture.',
                'price': Decimal('34.99'),
                'compare_price': Decimal('44.99'),
                'stock': 400,
                'rating': Decimal('4.55'),
                'num_reviews': 8500,
                'image_url': 'https://placehold.co/600x600/533483/fff?text=System+Design',
            },
        ],
    },
    'Gaming': {
        'description': 'Consoles, controllers & gaming gear',
        'icon': '🎮',
        'products': [
            {
                'name': 'PlayStation 5 Slim',
                'description': 'Sony PS5 Slim with 1TB SSD, DualSense controller, 4K gaming at 120fps, ray tracing, backward compatibility.',
                'price': Decimal('449.99'),
                'compare_price': Decimal('499.99'),
                'stock': 40,
                'rating': Decimal('4.80'),
                'num_reviews': 9800,
                'image_url': 'https://placehold.co/600x600/6c63ff/fff?text=PS5+Slim',
            },
            {
                'name': 'Nintendo Switch 2',
                'description': 'Nintendo Switch 2 with 8-inch LCD, enhanced Joy-Con controllers, DLSS support, backward compatible with Switch games.',
                'price': Decimal('399.99'),
                'compare_price': Decimal('449.99'),
                'stock': 60,
                'rating': Decimal('4.75'),
                'num_reviews': 3400,
                'image_url': 'https://placehold.co/600x600/e94560/fff?text=Switch+2',
            },
        ],
    },
    'Watches': {
        'description': 'Smart watches & luxury timepieces',
        'icon': '⌚',
        'products': [
            {
                'name': 'Apple Watch Ultra 3',
                'description': 'Apple Watch Ultra 3 with 49mm titanium case, precision dual-frequency GPS, 72-hour battery, dive computer, S10 chip.',
                'price': Decimal('799.99'),
                'compare_price': Decimal('899.99'),
                'stock': 30,
                'rating': Decimal('4.85'),
                'num_reviews': 1200,
                'image_url': 'https://placehold.co/600x600/16213e/fff?text=Watch+Ultra',
            },
            {
                'name': 'Samsung Galaxy Watch 7',
                'description': 'Samsung Galaxy Watch 7 with BioActive sensor, body composition, sleep tracking, Wear OS, 40-hour battery.',
                'price': Decimal('299.99'),
                'compare_price': Decimal('349.99'),
                'stock': 80,
                'rating': Decimal('4.50'),
                'num_reviews': 2800,
                'image_url': 'https://placehold.co/600x600/1a1a2e/fff?text=Galaxy+Watch',
            },
        ],
    },
    'Sports & Fitness': {
        'description': 'Equipment, gear & fitness accessories',
        'icon': '🏋️',
        'products': [
            {
                'name': 'Peloton Bike+',
                'description': 'Peloton Bike+ with 24-inch rotating HD touchscreen, auto-follow resistance, Apple GymKit, built-in speaker system.',
                'price': Decimal('2495.00'),
                'compare_price': Decimal('2795.00'),
                'stock': 10,
                'rating': Decimal('4.70'),
                'num_reviews': 3500,
                'image_url': 'https://placehold.co/600x600/0f3460/fff?text=Peloton',
            },
            {
                'name': 'Theragun PRO Plus',
                'description': 'Therabody Theragun PRO Plus percussive therapy device with smart app integration, 6 attachments, QuietForce technology.',
                'price': Decimal('399.99'),
                'compare_price': Decimal('449.99'),
                'stock': 70,
                'rating': Decimal('4.65'),
                'num_reviews': 1800,
                'image_url': 'https://placehold.co/600x600/533483/fff?text=Theragun',
            },
        ],
    },
    'Beauty & Care': {
        'description': 'Skincare, makeup & personal care',
        'icon': '💄',
        'products': [
            {
                'name': 'Dyson Airwrap Complete',
                'description': 'Dyson Airwrap multi-styler with Coanda airflow technology. Curl, wave, smooth, and dry with no extreme heat damage.',
                'price': Decimal('499.99'),
                'compare_price': Decimal('599.99'),
                'stock': 55,
                'rating': Decimal('4.75'),
                'num_reviews': 4100,
                'image_url': 'https://placehold.co/600x600/e94560/fff?text=Airwrap',
            },
            {
                'name': 'La Mer Moisturizing Cream',
                'description': 'La Mer The Moisturizing Cream 60ml. Miracle Broth infused for ultimate hydration, renewal, and radiance.',
                'price': Decimal('345.00'),
                'compare_price': Decimal('380.00'),
                'stock': 40,
                'rating': Decimal('4.80'),
                'num_reviews': 6200,
                'image_url': 'https://placehold.co/600x600/6c63ff/fff?text=La+Mer',
            },
        ],
    },
}

VND_PRICE_RANGES = {
    'Smartphones': (Decimal('5000000'), Decimal('45000000')),
    'Laptops': (Decimal('12000000'), Decimal('80000000')),
    'Audio': (Decimal('300000'), Decimal('25000000')),
    'Clothing': (Decimal('150000'), Decimal('4000000')),
    'Shoes': (Decimal('300000'), Decimal('7000000')),
    'Home Appliances': (Decimal('800000'), Decimal('50000000')),
    'Kitchen': (Decimal('100000'), Decimal('15000000')),
    'Books': (Decimal('80000'), Decimal('700000')),
    'Gaming': (Decimal('500000'), Decimal('50000000')),
    'Watches': (Decimal('500000'), Decimal('45000000')),
    'Sports & Fitness': (Decimal('150000'), Decimal('60000000')),
    'Beauty & Care': (Decimal('90000'), Decimal('12000000')),
}

CATEGORY_IMAGE_KEYWORDS = {
    'Smartphones': 'smartphone',
    'Laptops': 'laptop',
    'Audio': 'headphones',
    'Clothing': 'fashion',
    'Shoes': 'sneakers',
    'Home Appliances': 'home-appliance',
    'Kitchen': 'kitchen',
    'Books': 'book',
    'Gaming': 'gaming',
    'Watches': 'watch',
    'Sports & Fitness': 'fitness',
    'Beauty & Care': 'skincare',
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


def _build_image_url(category_name, product_name, lock_id):
    category_keyword = CATEGORY_IMAGE_KEYWORDS.get(category_name, 'product')
    name_tokens = [_slug_token(t) for t in product_name.split()[:3]]
    keywords = [category_keyword] + [t for t in name_tokens if t not in {'pro', 'max', 'plus'}]
    deduped_keywords = []
    for token in keywords:
        if token and token not in deduped_keywords:
            deduped_keywords.append(token)
    keyword_string = ','.join(deduped_keywords[:3])
    return f'https://loremflickr.com/1200/900/{keyword_string}?lock={lock_id}'


def _build_category_image_url(category_name, lock_id):
    keyword = CATEGORY_IMAGE_KEYWORDS.get(category_name, 'shopping')
    return f'https://loremflickr.com/900/600/{keyword}?lock={lock_id}'


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
    return f'{slugify(name)}-vn-{cycle}'


def _variant_name(template_name, cycle):
    if cycle == 1:
        return template_name
    return f'{template_name} Vietnam Edition {cycle}'


def _variant_description(template_description, cycle):
    if cycle == 1:
        return (
            f'{template_description} Official Vietnam market pricing, '
            'genuine warranty, and nationwide delivery support.'
        )
    return (
        f'{template_description} Vietnam market variant {cycle} with optimized '
        'pricing, genuine warranty, and fast nationwide delivery.'
    )


class Command(BaseCommand):
    help = 'Seed product catalog with Vietnam pricing and image URLs (default: 240 products).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-category',
            type=int,
            default=20,
            help='How many products to maintain in each category (default: 20, total: 240).',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=2026,
            help='Random seed for deterministic catalog generation.',
        )

    def handle(self, *args, **options):
        per_category = max(1, options['per_category'])
        rng = random.Random(options['seed'])
        target_total = per_category * len(SEED_DATA)

        self.stdout.write(
            f'Seeding product catalog with Vietnam pricing ({per_category} items/category, target {target_total} products)...'
        )

        created_count = 0
        updated_count = 0

        for category_index, (category_name, cat_data) in enumerate(SEED_DATA.items(), start=1):
            category_defaults = {
                'description': cat_data['description'],
                'image_url': _build_category_image_url(category_name, 7000 + category_index),
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
                expected_category_image = _build_category_image_url(category_name, 7000 + category_index)
                if category.image_url != expected_category_image:
                    category.image_url = expected_category_image
                    category_changed = True
                if category_changed:
                    category.save(update_fields=['description', 'image_url'])

            self.stdout.write(f'  Category: {category_name}')

            templates = cat_data['products']
            for i in range(per_category):
                template = templates[i % len(templates)]
                cycle = (i // len(templates)) + 1
                lock_id = (category_index * 1000) + i + 1

                name = _variant_name(template['name'], cycle)
                slug = _build_slug(template['name'], cycle)
                description = _variant_description(template['description'], cycle)

                price = _price_to_vnd(category_name, template['price'], cycle, rng)
                compare_price = _build_compare_price(price, category_name, rng)
                stock = _build_stock(template['stock'], cycle, rng)
                rating = _build_rating(template.get('rating', Decimal('4.20')), rng)
                num_reviews = _build_reviews(template.get('num_reviews', 120), cycle, rng)
                image_url = _build_image_url(category_name, name, lock_id)

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
                    self.stdout.write(f'    + Created: {name}')
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
                f'Seeding complete. Target {target_total} products, created {created_count}, updated {updated_count}.'
            )
        )
