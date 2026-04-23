"""
User Behavior Data Generator for AI Service.

Generates a synthetic dataset (data_user500.csv) with 500 users
and 8 behavior action types, simulating realistic e-commerce
user interactions.

This module ONLY generates behavior data. It reads existing user
and product UUIDs from the databases. User seeding is handled
separately by the `seed_users` management command.

8 Action Types (covering the full customer journey funnel):
    1. view        - User views a product page
    2. click       - User clicks on a product (from listing/search)
    3. search      - User searches for a product
    4. add_to_cart - User adds a product to their shopping cart
    5. add_to_wishlist - User adds a product to wishlist
    6. purchase    - User completes a purchase
    7. review      - User writes a review for a product
    8. share       - User shares a product on social media

The data follows a realistic funnel distribution:
    view > click > search > add_to_cart > add_to_wishlist > purchase > review > share
"""

import csv
import os
import random
import logging
from datetime import datetime, timedelta

import numpy as np

logger = logging.getLogger(__name__)

# 8 action types with realistic funnel probabilities
ACTION_WEIGHTS = {
    'view': 0.35,
    'click': 0.22,
    'search': 0.13,
    'add_to_cart': 0.10,
    'add_to_wishlist': 0.07,
    'purchase': 0.06,
    'review': 0.04,
    'share': 0.03,
}

ACTIONS = list(ACTION_WEIGHTS.keys())
PROBABILITIES = list(ACTION_WEIGHTS.values())

# Time range: last 90 days
END_DATE = datetime(2026, 4, 22, 23, 59, 59)
START_DATE = END_DATE - timedelta(days=90)


# ──────────────────────────────────────────────
# Database readers (read-only, no writes)
# ──────────────────────────────────────────────

def _db_config():
    """Return shared PostgreSQL connection parameters."""
    return {
        'host': os.environ.get('DATABASE_HOST', 'ecommerce-db'),
        'port': os.environ.get('DATABASE_PORT', '5432'),
        'user': os.environ.get('DATABASE_USER', 'postgres'),
        'password': os.environ.get('DATABASE_PASSWORD', 'postgres'),
    }


def fetch_user_ids():
    """Fetch all active user UUIDs from user_db (read-only)."""
    try:
        import psycopg2
        conn = psycopg2.connect(dbname='user_db', **_db_config())
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE is_active = true ORDER BY created_at")
        ids = [str(row[0]) for row in cur.fetchall()]
        cur.close()
        conn.close()
        logger.info(f"Fetched {len(ids)} users from user_db")
        return ids
    except Exception as e:
        logger.error(f"Could not read user_db: {e}")
        return []


def fetch_product_ids():
    """Fetch all active product UUIDs from product_db (read-only)."""
    try:
        import psycopg2
        conn = psycopg2.connect(dbname='product_db', **_db_config())
        cur = conn.cursor()
        cur.execute("SELECT id FROM products WHERE is_active = true ORDER BY created_at")
        ids = [str(row[0]) for row in cur.fetchall()]
        cur.close()
        conn.close()
        logger.info(f"Fetched {len(ids)} products from product_db")
        return ids
    except Exception as e:
        logger.error(f"Could not read product_db: {e}")
        return []


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _random_timestamp():
    """Generate a random timestamp within the 90-day window."""
    delta = END_DATE - START_DATE
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return START_DATE + timedelta(seconds=random_seconds)


def _generate_user_profile(user_id):
    """
    Generate a user profile that determines browsing behavior.

    Different user types have different activity patterns:
    - Power users (10%): Very active, many purchases
    - Regular users (60%): Moderate activity
    - Casual browsers (30%): Mostly views, few purchases
    """
    rand = random.random()
    if rand < 0.10:
        return {
            'user_id': user_id,
            'type': 'power',
            'num_events': random.randint(150, 300),
            'product_range': random.randint(30, 80),
            'purchase_boost': 2.5,
        }
    elif rand < 0.70:
        return {
            'user_id': user_id,
            'type': 'regular',
            'num_events': random.randint(60, 150),
            'product_range': random.randint(15, 50),
            'purchase_boost': 1.0,
        }
    else:
        return {
            'user_id': user_id,
            'type': 'casual',
            'num_events': random.randint(20, 60),
            'product_range': random.randint(5, 20),
            'purchase_boost': 0.3,
        }


# ──────────────────────────────────────────────
# Main generator
# ──────────────────────────────────────────────

def generate_behavior_data(output_path=None, stdout=None):
    """
    Generate the data_user500.csv dataset using REAL user and product UUIDs.

    Assumes users have already been seeded by the `seed_users` command.

    Steps:
    1. Read existing user UUIDs from user_db
    2. Read product UUIDs from product_db
    3. Generate behavior records using real UUIDs
    4. Write to CSV

    Args:
        output_path: Path to save the CSV file. If None, uses default data dir.
        stdout: Optional stdout for management command output.

    Returns:
        tuple of (stats dict, list of records)
    """
    if output_path is None:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        output_path = os.path.join(data_dir, 'data_user500.csv')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def _log(msg):
        logger.info(msg)
        if stdout:
            stdout.write(msg)

    # ── Step 1: Read users ────────────────
    _log("Step 1: Reading user UUIDs from user_db...")
    user_ids = fetch_user_ids()
    _log(f"  Found {len(user_ids)} users")

    if not user_ids:
        _log("  ERROR: No users found! Run 'seed_users' first.")
        return {'error': 'No users in user_db. Run seed_users first.'}, []

    # ── Step 2: Read products ─────────────
    _log("Step 2: Reading product UUIDs from product_db...")
    product_ids = fetch_product_ids()
    _log(f"  Found {len(product_ids)} products")

    if not product_ids:
        _log("  ERROR: No products found in product_db!")
        return {'error': 'No products in product_db.'}, []

    # ── Step 3: Generate behavior records ─
    _log(f"Step 3: Generating behavior records "
         f"({len(user_ids)} users × {len(product_ids)} products)...")

    random.seed(42)
    np.random.seed(42)

    all_records = []
    action_counts = {a: 0 for a in ACTIONS}

    for user_id in user_ids:
        profile = _generate_user_profile(user_id)
        num_events = profile['num_events']
        product_range = min(profile['product_range'], len(product_ids))

        # Each user interacts with a subset of real products
        user_products = random.sample(product_ids, product_range)

        # Adjust action probabilities based on user type
        user_probs = list(PROBABILITIES)
        if profile['type'] == 'power':
            user_probs[5] *= profile['purchase_boost']
            user_probs[6] *= 2.0
            user_probs[7] *= 2.0
        elif profile['type'] == 'casual':
            user_probs[0] *= 1.5
            user_probs[5] *= profile['purchase_boost']
            user_probs[6] *= 0.2
            user_probs[7] *= 0.2

        # Normalize probabilities
        total_prob = sum(user_probs)
        user_probs = [p / total_prob for p in user_probs]

        # Generate events for this user
        for _ in range(num_events):
            action = np.random.choice(ACTIONS, p=user_probs)

            # Product selection: users tend to interact with some products more
            if random.random() < 0.6:
                fav_count = max(1, len(user_products) // 3)
                product_id = random.choice(user_products[:fav_count])
            else:
                product_id = random.choice(user_products)

            timestamp = _random_timestamp()

            all_records.append({
                'user_id': user_id,
                'product_id': product_id,
                'action': action,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            })
            action_counts[action] += 1

    # Sort by timestamp
    all_records.sort(key=lambda x: x['timestamp'])

    # ── Step 4: Write to CSV ──────────────
    _log(f"Step 4: Writing {len(all_records)} records to {output_path} ...")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, fieldnames=['user_id', 'product_id', 'action', 'timestamp'])
        writer.writeheader()
        writer.writerows(all_records)

    stats = {
        'total_records': len(all_records),
        'total_users': len(user_ids),
        'total_products': len(set(r['product_id'] for r in all_records)),
        'action_types': ACTIONS,
        'action_distribution': action_counts,
        'date_range': {
            'start': START_DATE.strftime('%Y-%m-%d'),
            'end': END_DATE.strftime('%Y-%m-%d'),
        },
        'csv_path': output_path,
    }

    _log(f"Done! Generated {stats['total_records']} records "
         f"for {stats['total_users']} users")

    return stats, all_records
