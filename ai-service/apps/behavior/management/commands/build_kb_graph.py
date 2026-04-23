"""
Django management command to build Knowledge Base Graph in Neo4j
from user behavior data.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Build Knowledge Base Graph (KB_Graph) in Neo4j from behavior data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv', type=str, default=None,
            help='Path to data_user500.csv',
        )
        parser.add_argument(
            '--stats-only', action='store_true',
            help='Only show graph statistics, do not rebuild',
        )

    def handle(self, *args, **options):
        from apps.behavior.ml.kb_graph import build_kb_graph, _get_graph_stats

        data_dir = getattr(
            settings, 'DATA_DIR',
            os.path.join(settings.BASE_DIR, 'data'),
        )
        csv_path = options['csv'] or os.path.join(data_dir, 'data_user500.csv')

        if options['stats_only']:
            self.stdout.write(self.style.MIGRATE_HEADING(
                'KB Graph Statistics'))
            stats = _get_graph_stats()
            if stats:
                self.stdout.write(f"  Total Nodes:    {stats.get('total_nodes')}")
                self.stdout.write(f"  Total Rels:     {stats.get('total_rels')}")
                self.stdout.write(f"  Users:          {stats.get('users')}")
                self.stdout.write(f"  Products:       {stats.get('products')}")
                self.stdout.write(f"  Categories:     {stats.get('categories')}")
                self.stdout.write(f"  Actions:        {stats.get('actions')}")
                self.stdout.write(f"\n  Relationship types:")
                for rel_type, count in stats.get('rel_types', {}).items():
                    self.stdout.write(f"    {rel_type:>20s}: {count}")
            else:
                self.stdout.write(self.style.ERROR('  Could not connect to Neo4j'))
            return

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(
                f'CSV not found: {csv_path}'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            'Building Knowledge Base Graph'))
        self.stdout.write(f'  CSV:    {csv_path}')
        self.stdout.write(f'  Neo4j:  {os.environ.get("NEO4J_URI", "bolt://neo4j-db:7687")}')

        stats = build_kb_graph(csv_path, stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS(
            '\n★ KB Graph built successfully in Neo4j!'))
        self.stdout.write(
            f'  Open Neo4j Browser: http://localhost:7474')
