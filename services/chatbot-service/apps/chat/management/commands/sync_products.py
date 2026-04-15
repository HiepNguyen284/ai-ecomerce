"""
sync_products management command
---------------------------------
Fetches all products from product-service and indexes them
into ChromaDB for the RAG chatbot.
"""
from django.core.management.base import BaseCommand
from apps.chat.knowledge_base import fetch_all_products
from apps.chat import rag_engine


class Command(BaseCommand):
    help = 'Sync products from product-service into ChromaDB for RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum retries if product-service is not ready',
        )

    def handle(self, *args, **options):
        import time

        max_retries = options['max_retries']

        for attempt in range(1, max_retries + 1):
            self.stdout.write(f'Attempt {attempt}/{max_retries}: Fetching products...')

            products = fetch_all_products()
            if products:
                break

            if attempt < max_retries:
                self.stdout.write(self.style.WARNING(
                    f'No products found. Retrying in 5 seconds...'
                ))
                time.sleep(5)

        if not products:
            self.stdout.write(self.style.WARNING(
                'No products fetched. ChromaDB index will be empty. '
                'Chatbot will still work but cannot recommend specific products.'
            ))
            return

        self.stdout.write(f'Fetched {len(products)} products. Indexing into ChromaDB...')

        count = rag_engine.index_products(products)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully indexed {count} products into ChromaDB!'
        ))
