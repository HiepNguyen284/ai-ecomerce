"""
sync_products management command
---------------------------------
Fetches all products from product-service and indexes them
into Neo4j Knowledge Graph for the RAG chatbot.
"""
from django.core.management.base import BaseCommand
from apps.chat.knowledge_base import fetch_all_products
from apps.chat import rag_engine


class Command(BaseCommand):
    help = 'Sync products from product-service into Neo4j Knowledge Graph for RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum retries if product-service is not ready',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            default=True,
            help='Clear Neo4j graph before indexing new products (default: enabled)',
        )
        parser.add_argument(
            '--no-clear-existing',
            action='store_false',
            dest='clear_existing',
            help='Do not clear Neo4j graph before indexing',
        )

    def handle(self, *args, **options):
        import time

        max_retries = options['max_retries']
        clear_existing = options['clear_existing']

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
                'No products fetched. Neo4j index will be empty. '
                'Chatbot will still work but cannot recommend specific products.'
            ))
            return

        self.stdout.write(f'Fetched {len(products)} products. Indexing into Neo4j...')

        if clear_existing:
            deleted_nodes = rag_engine.clear_knowledge_graph()
            self.stdout.write(
                self.style.WARNING(
                    f'Cleared Neo4j graph before sync. Deleted nodes: {deleted_nodes}'
                )
            )

        count = rag_engine.index_products(products)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully indexed {count} products into Neo4j Knowledge Graph!'
        ))
