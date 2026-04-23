"""
Knowledge Base Graph Builder for Neo4j.

Builds a graph database from user behavior data with the schema:

Nodes:
  (:User {uuid, username, type})
  (:Product {uuid, name, category})
  (:Category {name})
  (:Action {name})

Relationships:
  (:User)-[:PERFORMED {timestamp, count}]->(:Action)
  (:User)-[:INTERACTED {action, timestamp, count}]->(:Product)
  (:Product)-[:BELONGS_TO]->(:Category)
  (:User)-[:VIEWED]->(:Product)
  (:User)-[:CLICKED]->(:Product)
  (:User)-[:SEARCHED]->(:Product)
  (:User)-[:ADDED_TO_CART]->(:Product)
  (:User)-[:ADDED_TO_WISHLIST]->(:Product)
  (:User)-[:PURCHASED]->(:Product)
  (:User)-[:REVIEWED]->(:Product)
  (:User)-[:SHARED]->(:Product)
  (:User)-[:SIMILAR_TO {score}]->(:User)  (co-interaction similarity)
"""

import os
import logging
import csv
from collections import defaultdict

logger = logging.getLogger(__name__)

# Map CSV action names to Neo4j relationship types
ACTION_TO_REL = {
    'view': 'VIEWED',
    'click': 'CLICKED',
    'search': 'SEARCHED',
    'add_to_cart': 'ADDED_TO_CART',
    'add_to_wishlist': 'ADDED_TO_WISHLIST',
    'purchase': 'PURCHASED',
    'review': 'REVIEWED',
    'share': 'SHARED',
}


def _get_neo4j_driver():
    """Create a Neo4j driver from environment variables."""
    from neo4j import GraphDatabase

    uri = os.environ.get('NEO4J_URI', 'bolt://neo4j-db:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'password')

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def _get_db_connection(dbname):
    """Get PostgreSQL connection to fetch extra info."""
    try:
        import psycopg2
        return psycopg2.connect(
            host=os.environ.get('DATABASE_HOST', 'ecommerce-db'),
            port=os.environ.get('DATABASE_PORT', '5432'),
            user=os.environ.get('DATABASE_USER', 'postgres'),
            password=os.environ.get('DATABASE_PASSWORD', 'postgres'),
            dbname=dbname,
        )
    except Exception as e:
        logger.warning(f"Could not connect to {dbname}: {e}")
        return None


def _fetch_user_info():
    """Fetch user details from user_db."""
    users = {}
    conn = _get_db_connection('user_db')
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, username, email, first_name, last_name
                FROM users WHERE is_active = true
            """)
            for row in cur.fetchall():
                users[str(row[0])] = {
                    'uuid': str(row[0]),
                    'username': row[1],
                    'email': row[2],
                    'first_name': row[3] or '',
                    'last_name': row[4] or '',
                }
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Error fetching users: {e}")
    return users


def _fetch_product_info():
    """Fetch product details with categories from product_db."""
    products = {}
    categories = set()
    conn = _get_db_connection('product_db')
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.name, p.slug, p.price, c.name as category
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = true
            """)
            for row in cur.fetchall():
                cat = row[4] or 'Unknown'
                products[str(row[0])] = {
                    'uuid': str(row[0]),
                    'name': row[1],
                    'slug': row[2],
                    'price': float(row[3]),
                    'category': cat,
                }
                categories.add(cat)
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Error fetching products: {e}")
    return products, categories


def _load_behavior_data(csv_path):
    """Load behavior CSV and aggregate interactions."""
    interactions = []
    user_action_counts = defaultdict(lambda: defaultdict(int))
    user_product_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row['user_id']
            pid = row['product_id']
            action = row['action']
            ts = row['timestamp']

            interactions.append({
                'user_id': uid,
                'product_id': pid,
                'action': action,
                'timestamp': ts,
            })
            user_action_counts[uid][action] += 1
            user_product_counts[uid][pid][action] += 1

    return interactions, user_action_counts, user_product_counts


def _compute_user_similarity(user_product_counts, top_k=5):
    """
    Compute user similarity based on co-interacted products.
    Uses Jaccard similarity on product sets.
    """
    user_products = {}
    for uid, products in user_product_counts.items():
        user_products[uid] = set(products.keys())

    similarities = []
    user_ids = list(user_products.keys())

    # For efficiency, sample if too many users
    import random
    if len(user_ids) > 200:
        user_ids = random.sample(user_ids, 200)

    for i in range(len(user_ids)):
        uid_a = user_ids[i]
        prods_a = user_products[uid_a]
        best_sims = []

        for j in range(len(user_ids)):
            if i == j:
                continue
            uid_b = user_ids[j]
            prods_b = user_products[uid_b]

            intersection = len(prods_a & prods_b)
            union = len(prods_a | prods_b)
            if union > 0:
                sim = intersection / union
                if sim > 0.15:  # Only keep meaningful similarities
                    best_sims.append((uid_b, sim))

        # Keep top_k similar users
        best_sims.sort(key=lambda x: -x[1])
        for uid_b, sim in best_sims[:top_k]:
            similarities.append((uid_a, uid_b, round(sim, 4)))

    return similarities


def build_kb_graph(csv_path, stdout=None):
    """
    Build the complete Knowledge Base Graph in Neo4j.

    Steps:
    1. Clear existing graph
    2. Create constraints and indexes
    3. Create Category nodes
    4. Create Product nodes + BELONGS_TO
    5. Create User nodes
    6. Create Action nodes
    7. Create behavior relationships (VIEWED, CLICKED, etc.)
    8. Create user-action aggregate relationships (PERFORMED)
    9. Compute and create SIMILAR_TO relationships
    """
    def _log(msg):
        logger.info(msg)
        if stdout:
            stdout.write(msg)
        print(msg)

    driver = _get_neo4j_driver()

    _log("Step 1: Loading data...")
    interactions, user_action_counts, user_product_counts = \
        _load_behavior_data(csv_path)
    _log(f"  Loaded {len(interactions)} interactions")

    _log("Step 2: Fetching user and product info from databases...")
    user_info = _fetch_user_info()
    product_info, categories = _fetch_product_info()
    _log(f"  Users: {len(user_info)}, Products: {len(product_info)}, "
         f"Categories: {len(categories)}")

    # Collect unique IDs from CSV (fallback if DB fetch fails)
    csv_user_ids = set(i['user_id'] for i in interactions)
    csv_product_ids = set(i['product_id'] for i in interactions)

    with driver.session() as session:
        # ── Step 3: Clear and setup ──
        _log("Step 3: Clearing existing graph and creating indexes...")
        session.run("MATCH (n) DETACH DELETE n")
        _try_create_constraint(session, "CREATE CONSTRAINT IF NOT EXISTS "
                               "FOR (u:User) REQUIRE u.uuid IS UNIQUE")
        _try_create_constraint(session, "CREATE CONSTRAINT IF NOT EXISTS "
                               "FOR (p:Product) REQUIRE p.uuid IS UNIQUE")
        _try_create_constraint(session, "CREATE CONSTRAINT IF NOT EXISTS "
                               "FOR (c:Category) REQUIRE c.name IS UNIQUE")
        _try_create_constraint(session, "CREATE CONSTRAINT IF NOT EXISTS "
                               "FOR (a:Action) REQUIRE a.name IS UNIQUE")

        # ── Step 4: Create Action nodes ──
        _log("Step 4: Creating Action nodes...")
        actions = list(ACTION_TO_REL.keys())
        for action in actions:
            session.run(
                "MERGE (a:Action {name: $name})",
                name=action,
            )
        _log(f"  Created {len(actions)} Action nodes")

        # ── Step 5: Create Category nodes ──
        _log("Step 5: Creating Category nodes...")
        for cat in categories:
            session.run(
                "MERGE (c:Category {name: $name})",
                name=cat,
            )
        _log(f"  Created {len(categories)} Category nodes")

        # ── Step 6: Create Product nodes ──
        _log("Step 6: Creating Product nodes...")
        product_batch = []
        for pid in csv_product_ids:
            info = product_info.get(pid, {})
            product_batch.append({
                'uuid': pid,
                'name': info.get('name', f'Product-{pid[:8]}'),
                'slug': info.get('slug', ''),
                'price': info.get('price', 0),
                'category': info.get('category', 'Unknown'),
            })

        # Batch create products
        session.run("""
            UNWIND $batch AS p
            MERGE (prod:Product {uuid: p.uuid})
            SET prod.name = p.name,
                prod.slug = p.slug,
                prod.price = p.price
            WITH prod, p
            MERGE (c:Category {name: p.category})
            MERGE (prod)-[:BELONGS_TO]->(c)
        """, batch=product_batch)
        _log(f"  Created {len(product_batch)} Product nodes with BELONGS_TO")

        # ── Step 7: Create User nodes ──
        _log("Step 7: Creating User nodes...")
        user_batch = []
        for uid in csv_user_ids:
            info = user_info.get(uid, {})
            # Determine user type based on activity
            total_actions = sum(user_action_counts[uid].values())
            if total_actions >= 150:
                utype = 'power'
            elif total_actions >= 60:
                utype = 'regular'
            else:
                utype = 'casual'

            user_batch.append({
                'uuid': uid,
                'username': info.get('username', f'user-{uid[:8]}'),
                'email': info.get('email', ''),
                'type': utype,
                'total_actions': total_actions,
            })

        session.run("""
            UNWIND $batch AS u
            MERGE (user:User {uuid: u.uuid})
            SET user.username = u.username,
                user.email = u.email,
                user.type = u.type,
                user.total_actions = u.total_actions
        """, batch=user_batch)
        _log(f"  Created {len(user_batch)} User nodes")

        # ── Step 8: Create User-PERFORMED->Action relationships ──
        _log("Step 8: Creating PERFORMED relationships...")
        perf_batch = []
        for uid, action_counts in user_action_counts.items():
            for action, count in action_counts.items():
                perf_batch.append({
                    'user_uuid': uid,
                    'action': action,
                    'count': count,
                })

        session.run("""
            UNWIND $batch AS r
            MATCH (u:User {uuid: r.user_uuid})
            MATCH (a:Action {name: r.action})
            MERGE (u)-[rel:PERFORMED]->(a)
            SET rel.count = r.count
        """, batch=perf_batch)
        _log(f"  Created {len(perf_batch)} PERFORMED relationships")

        # ── Step 9: Create typed behavior relationships ──
        _log("Step 9: Creating behavior relationships (VIEWED, CLICKED, etc.)...")
        # Aggregate: user -> product -> action -> count
        rel_batch = []
        for uid, products in user_product_counts.items():
            for pid, action_counts in products.items():
                for action, count in action_counts.items():
                    rel_type = ACTION_TO_REL.get(action)
                    if rel_type:
                        rel_batch.append({
                            'user_uuid': uid,
                            'product_uuid': pid,
                            'action': action,
                            'rel_type': rel_type,
                            'count': count,
                        })

        # Process in batches of 5000 for performance
        batch_size = 5000
        total_rels = 0
        for i in range(0, len(rel_batch), batch_size):
            chunk = rel_batch[i:i + batch_size]

            # Create each action type separately (Cypher limitation)
            for action, rel_type in ACTION_TO_REL.items():
                action_chunk = [r for r in chunk if r['action'] == action]
                if action_chunk:
                    session.run(f"""
                        UNWIND $batch AS r
                        MATCH (u:User {{uuid: r.user_uuid}})
                        MATCH (p:Product {{uuid: r.product_uuid}})
                        MERGE (u)-[rel:{rel_type}]->(p)
                        SET rel.count = r.count
                    """, batch=action_chunk)

            total_rels += len(chunk)
            if (i + batch_size) % 10000 == 0 or i + batch_size >= len(rel_batch):
                _log(f"  Processed {min(i + batch_size, len(rel_batch))}"
                     f"/{len(rel_batch)} relationships...")

        _log(f"  Created {total_rels} behavior relationships")

        # ── Step 10: User similarity ──
        _log("Step 10: Computing user similarity (Jaccard on co-products)...")
        similarities = _compute_user_similarity(user_product_counts, top_k=5)
        if similarities:
            sim_batch = [
                {'user_a': s[0], 'user_b': s[1], 'score': s[2]}
                for s in similarities
            ]
            session.run("""
                UNWIND $batch AS s
                MATCH (a:User {uuid: s.user_a})
                MATCH (b:User {uuid: s.user_b})
                MERGE (a)-[rel:SIMILAR_TO]->(b)
                SET rel.score = s.score
            """, batch=sim_batch)
            _log(f"  Created {len(sim_batch)} SIMILAR_TO relationships")
        else:
            _log("  No significant similarities found")

    driver.close()

    # ── Summary ──
    stats = _get_graph_stats()

    _log(f"\n{'=' * 60}")
    _log(f"KB Graph built successfully!")
    _log(f"  Nodes:         {stats.get('total_nodes', 'N/A')}")
    _log(f"  Relationships: {stats.get('total_rels', 'N/A')}")
    _log(f"  Users:         {stats.get('users', 'N/A')}")
    _log(f"  Products:      {stats.get('products', 'N/A')}")
    _log(f"  Categories:    {stats.get('categories', 'N/A')}")
    _log(f"  Actions:       {stats.get('actions', 'N/A')}")
    _log(f"{'=' * 60}")

    return stats


def _try_create_constraint(session, query):
    """Try to create a constraint, skip if already exists."""
    try:
        session.run(query)
    except Exception:
        pass


def _get_graph_stats():
    """Query Neo4j for graph statistics."""
    try:
        driver = _get_neo4j_driver()
        with driver.session() as session:
            stats = {}

            result = session.run("MATCH (n) RETURN count(n) AS c")
            stats['total_nodes'] = result.single()['c']

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS c")
            stats['total_rels'] = result.single()['c']

            result = session.run("MATCH (u:User) RETURN count(u) AS c")
            stats['users'] = result.single()['c']

            result = session.run("MATCH (p:Product) RETURN count(p) AS c")
            stats['products'] = result.single()['c']

            result = session.run("MATCH (c:Category) RETURN count(c) AS c")
            stats['categories'] = result.single()['c']

            result = session.run("MATCH (a:Action) RETURN count(a) AS c")
            stats['actions'] = result.single()['c']

            # Relationship type counts
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            stats['rel_types'] = {
                record['type']: record['count']
                for record in result
            }

        driver.close()
        return stats
    except Exception as e:
        logger.error(f"Could not get graph stats: {e}")
        return {}


def query_user_graph(user_uuid):
    """Query all relationships for a specific user."""
    driver = _get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {uuid: $uuid})-[r]->(target)
            RETURN type(r) AS rel_type, labels(target) AS target_labels,
                   properties(target) AS target_props,
                   properties(r) AS rel_props
            ORDER BY rel_type
        """, uuid=user_uuid)
        data = [dict(record) for record in result]
    driver.close()
    return data


def query_product_users(product_uuid, action=None):
    """Query all users who interacted with a product."""
    driver = _get_neo4j_driver()
    with driver.session() as session:
        if action and action in ACTION_TO_REL:
            rel_type = ACTION_TO_REL[action]
            result = session.run(f"""
                MATCH (u:User)-[r:{rel_type}]->(p:Product {{uuid: $uuid}})
                RETURN u.uuid AS user_uuid, u.username AS username,
                       r.count AS count
                ORDER BY r.count DESC
            """, uuid=product_uuid)
        else:
            result = session.run("""
                MATCH (u:User)-[r]->(p:Product {uuid: $uuid})
                RETURN u.uuid AS user_uuid, u.username AS username,
                       type(r) AS action, r.count AS count
                ORDER BY r.count DESC
            """, uuid=product_uuid)
        data = [dict(record) for record in result]
    driver.close()
    return data


def query_similar_users(user_uuid, limit=10):
    """Find similar users via SIMILAR_TO relationships."""
    driver = _get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {uuid: $uuid})-[r:SIMILAR_TO]->(s:User)
            RETURN s.uuid AS user_uuid, s.username AS username,
                   s.type AS user_type, r.score AS similarity
            ORDER BY r.score DESC
            LIMIT $limit
        """, uuid=user_uuid, limit=limit)
        data = [dict(record) for record in result]
    driver.close()
    return data


def query_recommend_products(user_uuid, limit=10):
    """
    Recommend products based on graph traversal:
    User -> SIMILAR_TO -> Other Users -> PURCHASED -> Products
    (that current user hasn't purchased yet)
    """
    driver = _get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {uuid: $uuid})-[:SIMILAR_TO]->(sim:User)
                  -[:PURCHASED]->(p:Product)
            WHERE NOT (u)-[:PURCHASED]->(p)
            WITH p, count(DISTINCT sim) AS recommenders,
                 avg(sim.total_actions) AS avg_activity
            RETURN p.uuid AS product_uuid, p.name AS product_name,
                   p.price AS price, recommenders,
                   round(avg_activity) AS avg_recommender_activity
            ORDER BY recommenders DESC, avg_activity DESC
            LIMIT $limit
        """, uuid=user_uuid, limit=limit)
        data = [dict(record) for record in result]
    driver.close()
    return data
