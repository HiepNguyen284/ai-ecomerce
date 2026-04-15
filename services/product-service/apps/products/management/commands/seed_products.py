import random
import time
from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.products.models import Category, Product


class Command(BaseCommand):
    help = "Reset categories/products from DummyJSON, translate to Vietnamese, and convert prices to VND"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=0,
            help="Number of products to import. 0 means all products from DummyJSON.",
        )
        parser.add_argument(
            "--exchange-rate",
            type=int,
            default=26000,
            help="USD to VND exchange rate used for product prices.",
        )
        parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
        parser.add_argument(
            "--skip-translation",
            action="store_true",
            help="Keep source text without auto-translation.",
        )

    def handle(self, *args, **options):
        requested_count = max(0, int(options["count"]))
        exchange_rate = max(1, int(options["exchange_rate"]))
        timeout = max(5, int(options["timeout"]))
        skip_translation = bool(options["skip_translation"])

        self.translation_cache = {}

        self.stdout.write("Fetching categories from DummyJSON...")
        source_categories = self._fetch_dummy_categories(timeout=timeout)
        if len(source_categories) <= 10:
            raise CommandError("DummyJSON categories must be > 10 to continue.")

        self.stdout.write("Fetching products from DummyJSON...")
        source_products = self._fetch_dummy_products(timeout=timeout)
        if not source_products:
            raise CommandError("DummyJSON returned no products.")

        if requested_count > 0:
            source_products = source_products[:requested_count]

        with transaction.atomic():
            deleted_products, _ = Product.objects.all().delete()
            deleted_categories, _ = Category.objects.all().delete()

            categories, category_by_slug = self._create_categories(
                source_categories=source_categories,
                timeout=timeout,
                skip_translation=skip_translation,
            )

            if len(categories) <= 10:
                raise CommandError("Created category count is <= 10. Aborting.")

            products = self._build_products(
                source_products=source_products,
                category_by_slug=category_by_slug,
                categories=categories,
                exchange_rate=exchange_rate,
                timeout=timeout,
                skip_translation=skip_translation,
            )

            Product.objects.bulk_create(products, batch_size=200)

        distribution = {category.id: 0 for category in categories}
        for product in products:
            distribution[product.category_id] = distribution.get(product.category_id, 0) + 1

        self.stdout.write(self.style.SUCCESS(f"Deleted products: {deleted_products}"))
        self.stdout.write(self.style.SUCCESS(f"Deleted categories: {deleted_categories}"))
        self.stdout.write(self.style.SUCCESS(f"Created categories: {len(categories)}"))
        self.stdout.write(self.style.SUCCESS(f"Created products: {len(products)}"))
        self.stdout.write(f"Applied exchange rate (USD->VND): {exchange_rate}")
        self.stdout.write("Products by category:")
        for category in categories:
            amount = distribution.get(category.id, 0)
            self.stdout.write(f"  - {category.name}: {amount}")

    def _fetch_dummy_categories(self, timeout):
        response = requests.get("https://dummyjson.com/products/categories", timeout=timeout)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list):
            raise CommandError("Unexpected category payload format from DummyJSON.")

        normalized = []
        seen_slugs = set()
        for item in payload:
            if isinstance(item, dict):
                slug = str(item.get("slug") or "").strip().lower()
                name = str(item.get("name") or slug).strip()
            else:
                slug = str(item or "").strip().lower()
                name = slug.replace("-", " ").title()

            if not slug or slug in seen_slugs:
                continue

            seen_slugs.add(slug)
            normalized.append({"slug": slug, "name": name})

        return normalized

    def _fetch_dummy_products(self, timeout):
        all_products = []
        limit = 100
        skip = 0
        total = None

        while True:
            url = f"https://dummyjson.com/products?limit={limit}&skip={skip}"
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            payload = response.json()

            products = payload.get("products") or []
            if not products:
                break

            all_products.extend(products)
            total = payload.get("total", total)
            skip += len(products)

            if total is not None and skip >= int(total):
                break

        return all_products

    def _create_categories(self, source_categories, timeout, skip_translation):
        rows = []
        used_names = set()

        for index, item in enumerate(source_categories, start=1):
            slug = item["slug"]
            source_name = item["name"]

            translated_name = self._translate_text(
                text=source_name,
                timeout=timeout,
                skip_translation=skip_translation,
            )
            translated_name = translated_name.strip() or source_name

            unique_name = self._build_unique_category_name(translated_name, used_names)
            description_source = f"Products in category {source_name} are synced from DummyJSON."
            translated_description = self._translate_text(
                text=description_source,
                timeout=timeout,
                skip_translation=skip_translation,
            )

            image_query = slug.replace("-", ",")
            image_url = f"https://loremflickr.com/600/600/{image_query}?lock={5000 + index}"

            rows.append(
                {
                    "slug": slug,
                    "name": unique_name,
                    "description": translated_description,
                    "image_url": image_url,
                }
            )

        Category.objects.bulk_create(
            [
                Category(
                    name=row["name"],
                    description=row["description"],
                    image_url=row["image_url"],
                )
                for row in rows
            ],
            batch_size=100,
        )

        created_lookup = {
            category.name: category
            for category in Category.objects.filter(name__in=[row["name"] for row in rows])
        }

        categories = []
        category_by_slug = {}
        for row in rows:
            category = created_lookup[row["name"]]
            categories.append(category)
            category_by_slug[row["slug"]] = category

        return categories, category_by_slug

    def _build_products(
        self,
        source_products,
        category_by_slug,
        categories,
        exchange_rate,
        timeout,
        skip_translation,
    ):
        used_slugs = set()
        products = []

        for index, item in enumerate(source_products, start=1):
            title_source = str(item.get("title") or f"Product {index}").strip()
            description_source = str(item.get("description") or title_source).strip()

            title_vi = self._translate_text(
                text=title_source,
                timeout=timeout,
                skip_translation=skip_translation,
            )
            description_vi = self._translate_text(
                text=description_source,
                timeout=timeout,
                skip_translation=skip_translation,
            )

            category_slug = str(item.get("category") or "").strip().lower()
            category = category_by_slug.get(category_slug)
            if category is None:
                category = categories[(index - 1) % len(categories)]

            price_usd = self._to_decimal(item.get("price"), Decimal("0.00"))
            discount_percent = self._to_decimal(item.get("discountPercentage"), Decimal("0.00"))
            price_vnd = self._usd_to_vnd(price_usd, exchange_rate)
            compare_price_vnd = self._build_compare_price_vnd(price_usd, discount_percent, exchange_rate)

            rating = self._to_decimal(item.get("rating"), Decimal("0.00"))
            rating = min(Decimal("5.00"), max(Decimal("0.00"), rating))

            stock = item.get("stock")
            try:
                stock = max(0, int(stock))
            except (TypeError, ValueError):
                stock = 0

            image_url = item.get("thumbnail")
            if not image_url:
                images = item.get("images") or []
                image_url = images[0] if images else ""

            reviews = item.get("reviews") or []
            try:
                num_reviews = len(reviews)
            except TypeError:
                num_reviews = 0
            if num_reviews == 0:
                num_reviews = random.randint(10, 500)

            base_slug = slugify(title_vi) or slugify(title_source) or f"san-pham-{index}"
            slug = self._build_unique_slug(base_slug, used_slugs)

            products.append(
                Product(
                    name=(title_vi or title_source)[:255],
                    slug=slug,
                    description=description_vi or description_source,
                    price=price_vnd,
                    compare_price=compare_price_vnd,
                    category=category,
                    image_url=image_url,
                    stock=stock,
                    is_active=True,
                    rating=rating,
                    num_reviews=num_reviews,
                )
            )

        return products

    def _translate_text(self, text, timeout, skip_translation):
        source_text = str(text or "").strip()
        if not source_text:
            return ""

        if skip_translation:
            return source_text

        cached = self.translation_cache.get(source_text)
        if cached is not None:
            return cached

        endpoint = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "vi",
            "dt": "t",
            "q": source_text,
        }

        translated = source_text
        for _ in range(3):
            try:
                response = requests.get(endpoint, params=params, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
                translated_candidate = self._extract_translation(payload)
                if translated_candidate:
                    translated = translated_candidate
                    break
            except (requests.RequestException, ValueError, TypeError):
                time.sleep(0.2)

        self.translation_cache[source_text] = translated
        return translated

    def _extract_translation(self, payload):
        if not isinstance(payload, list) or not payload:
            return ""

        chunks = payload[0]
        if not isinstance(chunks, list):
            return ""

        text_parts = []
        for chunk in chunks:
            if isinstance(chunk, list) and chunk and isinstance(chunk[0], str):
                text_parts.append(chunk[0])
        return "".join(text_parts).strip()

    def _build_unique_category_name(self, category_name, used_names):
        base = (category_name or "Danh muc").strip()
        if not base:
            base = "Danh muc"

        base = base[:100]
        if base not in used_names:
            used_names.add(base)
            return base

        suffix = 2
        while True:
            marker = f" ({suffix})"
            candidate = f"{base[:100 - len(marker)]}{marker}"
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            suffix += 1

    def _build_unique_slug(self, base_slug, used_slugs):
        base = (base_slug or "san-pham").strip("-")
        if not base:
            base = "san-pham"

        base = base[:245]
        candidate = base
        suffix = 2
        while candidate in used_slugs:
            marker = f"-{suffix}"
            candidate = f"{base[:255 - len(marker)]}{marker}"
            suffix += 1

        used_slugs.add(candidate)
        return candidate

    def _to_decimal(self, value, default):
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            parsed = default
        return parsed.quantize(Decimal("0.01"))

    def _usd_to_vnd(self, usd_amount, exchange_rate):
        converted = (usd_amount * Decimal(str(exchange_rate))).quantize(Decimal("1"))
        return converted.quantize(Decimal("0.01"))

    def _build_compare_price_vnd(self, price_usd, discount_percent, exchange_rate):
        if discount_percent <= 0 or discount_percent >= 100:
            return None

        divisor = Decimal("1.00") - (discount_percent / Decimal("100.00"))
        if divisor <= 0:
            return None

        compare_price_usd = (price_usd / divisor).quantize(Decimal("0.01"))
        compare_price_vnd = self._usd_to_vnd(compare_price_usd, exchange_rate)
        current_price_vnd = self._usd_to_vnd(price_usd, exchange_rate)

        if compare_price_vnd <= current_price_vnd:
            return None
        return compare_price_vnd
