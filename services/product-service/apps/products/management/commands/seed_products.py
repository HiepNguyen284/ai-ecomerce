from decimal import Decimal
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


class Command(BaseCommand):
    help = 'Seed the database with initial product data (12 categories, 24 products)'

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING('Products already exist. Skipping seed.'))
            return

        self.stdout.write('Seeding categories and products...')
        total_products = 0

        for category_name, cat_data in SEED_DATA.items():
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': cat_data['description'],
                    'image_url': f'https://placehold.co/400x300/1a1a2e/fff?text={category_name.replace(" ", "+")}'
                }
            )
            self.stdout.write(f'  Category: {category_name}')

            for product_data in cat_data['products']:
                slug = slugify(product_data['name'])
                Product.objects.create(
                    name=product_data['name'],
                    slug=slug,
                    description=product_data['description'],
                    price=product_data['price'],
                    compare_price=product_data.get('compare_price'),
                    category=category,
                    image_url=product_data.get('image_url', ''),
                    stock=product_data['stock'],
                    rating=product_data.get('rating', Decimal('0.00')),
                    num_reviews=product_data.get('num_reviews', 0),
                    is_active=True,
                )
                total_products += 1
                self.stdout.write(f'    + {product_data["name"]}')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded {total_products} products in {len(SEED_DATA)} categories.'
        ))
