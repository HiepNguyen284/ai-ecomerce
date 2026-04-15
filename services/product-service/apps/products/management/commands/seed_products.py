from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product


SEED_DATA = {
    'Electronics': [
        {
            'name': 'iPhone 16 Pro Max',
            'description': 'Apple iPhone 16 Pro Max with A18 Pro chip, 6.9-inch Super Retina XDR display, 48MP camera system with 5x optical zoom, titanium design, and all-day battery life.',
            'price': Decimal('1199.99'),
            'compare_price': Decimal('1299.99'),
            'stock': 50,
            'rating': Decimal('4.85'),
            'num_reviews': 2340,
            'image_url': 'https://placehold.co/600x600/1a1a2e/eee?text=iPhone+16+Pro',
        },
        {
            'name': 'Samsung Galaxy S25 Ultra',
            'description': 'Samsung Galaxy S25 Ultra featuring Snapdragon 8 Elite, 6.9-inch Dynamic AMOLED 2X, 200MP camera, built-in S Pen, and Galaxy AI features.',
            'price': Decimal('1099.99'),
            'compare_price': Decimal('1199.99'),
            'stock': 35,
            'rating': Decimal('4.70'),
            'num_reviews': 1850,
            'image_url': 'https://placehold.co/600x600/16213e/eee?text=Galaxy+S25',
        },
        {
            'name': 'MacBook Pro 14" M4 Pro',
            'description': 'Apple MacBook Pro 14-inch with M4 Pro chip, 24GB unified memory, 1TB SSD, Liquid Retina XDR display, up to 17 hours of battery life.',
            'price': Decimal('1999.99'),
            'compare_price': Decimal('2199.99'),
            'stock': 20,
            'rating': Decimal('4.90'),
            'num_reviews': 980,
            'image_url': 'https://placehold.co/600x600/0f3460/eee?text=MacBook+Pro',
        },
        {
            'name': 'Sony WH-1000XM6 Headphones',
            'description': 'Sony premium wireless noise-cancelling headphones with industry-leading ANC, 40-hour battery, LDAC Hi-Res Audio, multipoint connection, and speak-to-chat.',
            'price': Decimal('349.99'),
            'compare_price': Decimal('399.99'),
            'stock': 100,
            'rating': Decimal('4.75'),
            'num_reviews': 3200,
            'image_url': 'https://placehold.co/600x600/533483/eee?text=Sony+XM6',
        },
    ],
    'Clothing': [
        {
            'name': 'Nike Air Max 270 React',
            'description': 'Nike Air Max 270 React running shoes combining two of Nike biggest innovations — Max Air and React foam — for a super-smooth, lightweight ride.',
            'price': Decimal('149.99'),
            'compare_price': Decimal('179.99'),
            'stock': 200,
            'rating': Decimal('4.50'),
            'num_reviews': 4500,
            'image_url': 'https://placehold.co/600x600/e94560/eee?text=Nike+Air+Max',
        },
        {
            'name': 'Levi\'s 501 Original Fit Jeans',
            'description': 'The iconic Levi\'s 501 Original Fit jeans with signature button fly, straight leg, and premium denim. A timeless wardrobe essential since 1873.',
            'price': Decimal('69.99'),
            'compare_price': Decimal('89.99'),
            'stock': 300,
            'rating': Decimal('4.40'),
            'num_reviews': 8900,
            'image_url': 'https://placehold.co/600x600/1a1a2e/eee?text=Levi+501',
        },
        {
            'name': 'Adidas Ultraboost Light',
            'description': 'Adidas Ultraboost Light running shoes — the lightest Ultraboost ever with BOOST midsole, Continental rubber outsole, and Primeknit+ upper.',
            'price': Decimal('189.99'),
            'compare_price': Decimal('219.99'),
            'stock': 150,
            'rating': Decimal('4.65'),
            'num_reviews': 2100,
            'image_url': 'https://placehold.co/600x600/0f3460/eee?text=Ultraboost',
        },
    ],
    'Home & Kitchen': [
        {
            'name': 'Dyson V15 Detect Vacuum',
            'description': 'Dyson V15 Detect cordless vacuum with laser dust detection, piezo sensor, LCD screen displaying real-time particle count, and up to 60 minutes of runtime.',
            'price': Decimal('649.99'),
            'compare_price': Decimal('749.99'),
            'stock': 30,
            'rating': Decimal('4.80'),
            'num_reviews': 1560,
            'image_url': 'https://placehold.co/600x600/533483/eee?text=Dyson+V15',
        },
        {
            'name': 'Instant Pot Duo Plus 6-Quart',
            'description': 'Instant Pot 9-in-1 pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker, warmer, sterilizer, and sous vide.',
            'price': Decimal('89.99'),
            'compare_price': Decimal('119.99'),
            'stock': 250,
            'rating': Decimal('4.70'),
            'num_reviews': 12000,
            'image_url': 'https://placehold.co/600x600/e94560/eee?text=Instant+Pot',
        },
        {
            'name': 'KitchenAid Artisan Stand Mixer',
            'description': 'KitchenAid Artisan Series 5-Quart tilt-head stand mixer with 10 speeds, stainless steel bowl, and planetary mixing action.',
            'price': Decimal('379.99'),
            'compare_price': Decimal('449.99'),
            'stock': 45,
            'rating': Decimal('4.85'),
            'num_reviews': 6700,
            'image_url': 'https://placehold.co/600x600/16213e/eee?text=KitchenAid',
        },
    ],
    'Books': [
        {
            'name': 'Clean Code by Robert C. Martin',
            'description': 'A handbook of agile software craftsmanship. Even bad code can function. But if code isn\'t clean, it can bring a development organization to its knees.',
            'price': Decimal('39.99'),
            'compare_price': Decimal('49.99'),
            'stock': 500,
            'rating': Decimal('4.60'),
            'num_reviews': 15000,
            'image_url': 'https://placehold.co/600x600/1a1a2e/eee?text=Clean+Code',
        },
        {
            'name': 'System Design Interview by Alex Xu',
            'description': 'An insider\'s guide to system design interviews. Covers scalability, distributed systems, microservices, and real-world architecture problems.',
            'price': Decimal('34.99'),
            'compare_price': Decimal('44.99'),
            'stock': 400,
            'rating': Decimal('4.55'),
            'num_reviews': 8500,
            'image_url': 'https://placehold.co/600x600/0f3460/eee?text=System+Design',
        },
    ],
}


class Command(BaseCommand):
    help = 'Seed the database with initial product data (>10 products)'

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING('Products already exist. Skipping seed.'))
            return

        self.stdout.write('Seeding categories and products...')
        total_products = 0

        for category_name, products in SEED_DATA.items():
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': f'All {category_name.lower()} products'}
            )
            self.stdout.write(f'  Category: {category_name}')

            for product_data in products:
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

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {total_products} products in {len(SEED_DATA)} categories.'))
