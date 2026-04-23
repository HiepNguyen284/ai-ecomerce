"""
Django management command to seed 500 users into user_db.

This is a SEPARATE step that runs BEFORE behavior data generation.
It creates users via the user-service API first, then falls back
to direct DB insertion if needed.

A temporary file (_seed_users_ids.txt) is written during execution
and deleted automatically when the command finishes.
"""
import os
import json
import logging
import requests
import uuid as uuid_module
from datetime import datetime

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

TARGET_USERS = 500
TEMP_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))), 'data', '_seed_users_ids.txt')


def _db_config():
    """Return database connection parameters from environment."""
    return {
        'host': os.environ.get('DATABASE_HOST', 'ecommerce-db'),
        'port': os.environ.get('DATABASE_PORT', '5432'),
        'user': os.environ.get('DATABASE_USER', 'postgres'),
        'password': os.environ.get('DATABASE_PASSWORD', 'postgres'),
    }


def _fetch_existing_users():
    """Fetch all active user UUIDs directly from user_db."""
    try:
        import psycopg2
        cfg = _db_config()
        conn = psycopg2.connect(dbname='user_db', **cfg)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE is_active = true ORDER BY created_at")
        ids = [str(row[0]) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return ids
    except Exception as e:
        logger.warning(f"Could not query user_db: {e}")
        return []


def _register_via_api(user_service_url, start_num, count, stdout):
    """Register users via user-service REST API."""
    created = []
    for i in range(count):
        num = start_num + i + 1
        payload = {
            'email': f'user{num}@ecommerce.ai',
            'username': f'user{num}',
            'password': 'AiUser@2026!',
            'password_confirm': 'AiUser@2026!',
            'first_name': 'User',
            'last_name': str(num),
        }
        try:
            resp = requests.post(
                f'{user_service_url}/users/register/',
                json=payload,
                timeout=10,
            )
            if resp.status_code == 201:
                uid = resp.json().get('user', {}).get('id')
                if uid:
                    created.append(str(uid))
            # 400 = duplicate email → skip silently
        except requests.RequestException:
            pass

        if (i + 1) % 50 == 0:
            stdout.write(f'    API registered {i + 1}/{count} ...')

    return created


def _insert_directly(start_num, count, stdout):
    """Insert users directly into user_db as a fallback."""
    created = []
    try:
        import psycopg2
        from django.contrib.auth.hashers import make_password

        cfg = _db_config()
        conn = psycopg2.connect(dbname='user_db', **cfg)
        cur = conn.cursor()
        hashed_pw = make_password('AiUser@2026!')
        now = datetime.now()

        for i in range(count):
            num = start_num + i + 1
            uid = str(uuid_module.uuid4())
            email = f'user{num}@ecommerce.ai'
            username = f'user{num}'

            try:
                cur.execute(
                    """
                    INSERT INTO users
                        (id, password, last_login, is_superuser,
                         username, first_name, last_name, email,
                         is_staff, is_active, date_joined,
                         phone, address, avatar_url,
                         created_at, updated_at)
                    VALUES (%s,%s,NULL,false,%s,%s,%s,%s,false,true,%s,'','','',%s,%s)
                    ON CONFLICT (email) DO NOTHING
                    RETURNING id
                    """,
                    (uid, hashed_pw, username, 'User', str(num),
                     email, now, now, now),
                )
                row = cur.fetchone()
                if row:
                    created.append(str(row[0]))
                else:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    existing = cur.fetchone()
                    if existing:
                        created.append(str(existing[0]))
            except Exception:
                conn.rollback()
                continue

            if (i + 1) % 100 == 0:
                conn.commit()
                stdout.write(f'    DB inserted {i + 1}/{count} ...')

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Direct DB insert failed: {e}")

    return created


class Command(BaseCommand):
    help = 'Seed 500 users into user_db (separate from behavior data generation)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-enough',
            action='store_true',
            help='Skip if user_db already has >= 500 active users',
        )
        parser.add_argument(
            '--target',
            type=int,
            default=TARGET_USERS,
            help='Target number of users (default: 500)',
        )

    def handle(self, *args, **options):
        target = options['target']
        user_service_url = os.environ.get(
            'USER_SERVICE_URL', 'http://user-service:8000')

        # Ensure data dir exists for temp file
        os.makedirs(os.path.dirname(TEMP_FILE), exist_ok=True)

        try:
            self._run(user_service_url, target, options['skip_if_enough'])
        finally:
            # Always clean up the temp file
            self._cleanup()

    def _run(self, user_service_url, target, skip_if_enough):
        self.stdout.write(self.style.MIGRATE_HEADING('Seed Users'))
        self.stdout.write(f'  Target: {target} users in user_db')

        # ── Step 1: count existing ──
        existing_ids = _fetch_existing_users()
        self.stdout.write(f'  Existing users: {len(existing_ids)}')

        if skip_if_enough and len(existing_ids) >= target:
            self.stdout.write(self.style.SUCCESS(
                f'  Already have {len(existing_ids)} users (>= {target}). Skipping.'))
            return

        needed = target - len(existing_ids)
        if needed <= 0:
            self.stdout.write(self.style.SUCCESS('  No new users needed.'))
            return

        self.stdout.write(f'  Need to create {needed} more users')

        # Write progress to temp file
        self._write_temp({'status': 'running', 'existing': len(existing_ids),
                          'needed': needed})

        # ── Step 2: register via API ──
        self.stdout.write('  Registering via user-service API...')
        api_ids = _register_via_api(
            user_service_url, len(existing_ids), needed, self.stdout)
        existing_ids.extend(api_ids)
        self.stdout.write(f'    → API created: {len(api_ids)}')

        # ── Step 3: fallback to direct DB insert ──
        still_needed = target - len(existing_ids)
        if still_needed > 0:
            self.stdout.write(
                f'  Still need {still_needed}. Inserting directly into user_db...')
            db_ids = _insert_directly(len(existing_ids), still_needed, self.stdout)
            existing_ids.extend(db_ids)
            self.stdout.write(f'    → DB created: {len(db_ids)}')

        # Final count
        final = _fetch_existing_users()
        self.stdout.write(self.style.SUCCESS(
            f'  Done! user_db now has {len(final)} active users'))

        self._write_temp({'status': 'done', 'total': len(final)})

    def _write_temp(self, data):
        """Write progress info to temp file."""
        try:
            with open(TEMP_FILE, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _cleanup(self):
        """Delete the temporary file."""
        try:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                self.stdout.write(f'  Cleaned up temp file: {TEMP_FILE}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'  Could not remove temp file: {e}'))
