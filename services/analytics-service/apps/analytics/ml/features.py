"""
Feature Engineering for Customer Behavior Analysis.

Transforms raw behavior events into structured feature vectors
suitable for deep learning model input.
"""

import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from django.utils import timezone


# Feature names used across the pipeline -- order matters!
STATIC_FEATURE_NAMES = [
    'recency_days', 'frequency', 'monetary',
    'avg_order_value', 'max_order_value', 'min_order_value',
    'total_items_purchased', 'unique_products', 'unique_categories',
    'avg_items_per_order', 'cancelled_ratio',
    'days_as_customer', 'order_frequency_monthly',
    'preferred_hour_sin', 'preferred_hour_cos',
    'preferred_dow_sin', 'preferred_dow_cos',
    'weekend_ratio',
]

# Number of dynamic category columns (padded/truncated to this)
NUM_CATEGORY_SLOTS = 12

# Total feature dimension = static + category + hour distribution (24) + dow (7)
TOTAL_FEATURE_DIM = len(STATIC_FEATURE_NAMES) + NUM_CATEGORY_SLOTS + 24 + 7


def extract_customer_features(events, customer_id, reference_date=None):
    """
    Extract a feature dictionary from a list of behavior events for one customer.

    Args:
        events: list of dicts with keys: event_type, amount, quantity, timestamp,
                product_id, product_name, category_name, metadata
        customer_id: UUID of the customer
        reference_date: datetime for computing recency (defaults to now)

    Returns:
        dict with all computed features
    """
    if reference_date is None:
        reference_date = timezone.now()

    # Separate purchase vs cancel events
    purchases = [e for e in events if e['event_type'] == 'purchase']
    cancels = [e for e in events if e['event_type'] == 'cancel']
    all_orders_count = len(purchases) + len(cancels)

    if not purchases:
        return _empty_features(customer_id)

    # === RFM ===
    purchase_dates = [e['timestamp'] for e in purchases]
    amounts = [float(e['amount']) for e in purchases]
    quantities = [int(e.get('quantity', 1)) for e in purchases]

    latest_purchase = max(purchase_dates)
    earliest_purchase = min(purchase_dates)
    recency_days = (reference_date - latest_purchase).days
    frequency = len(purchases)
    monetary = sum(amounts)

    # === Order stats ===
    avg_order_value = monetary / frequency if frequency > 0 else 0
    max_order_value = max(amounts)
    min_order_value = min(amounts)
    total_items = sum(quantities)
    avg_items = total_items / frequency if frequency > 0 else 0
    cancelled_ratio = len(cancels) / all_orders_count if all_orders_count > 0 else 0

    # === Time features ===
    days_as_customer = (reference_date - earliest_purchase).days
    months_active = max(days_as_customer / 30.0, 1)
    order_freq_monthly = frequency / months_active

    # Hour and day-of-week distributions
    hours = [e['timestamp'].hour for e in purchases]
    dows = [e['timestamp'].weekday() for e in purchases]

    hour_counter = Counter(hours)
    dow_counter = Counter(dows)
    preferred_hour = hour_counter.most_common(1)[0][0]
    preferred_dow = dow_counter.most_common(1)[0][0]

    # Cyclical encoding of time
    hour_sin = np.sin(2 * np.pi * preferred_hour / 24)
    hour_cos = np.cos(2 * np.pi * preferred_hour / 24)
    dow_sin = np.sin(2 * np.pi * preferred_dow / 7)
    dow_cos = np.cos(2 * np.pi * preferred_dow / 7)

    weekend_purchases = sum(1 for d in dows if d >= 5)
    weekend_ratio = weekend_purchases / len(dows) if dows else 0

    # Hour distribution (24-dim)
    hour_dist = np.zeros(24)
    for h, count in hour_counter.items():
        hour_dist[h] = count / len(hours)

    # Day-of-week distribution (7-dim)
    dow_dist = np.zeros(7)
    for d, count in dow_counter.items():
        dow_dist[d] = count / len(dows)

    # === Category features ===
    categories = [e.get('category_name', 'Unknown') for e in purchases]
    unique_products = len(set(e.get('product_id') for e in purchases if e.get('product_id')))
    unique_categories = len(set(categories))

    cat_counter = Counter(categories)
    total_cat = sum(cat_counter.values())
    category_distribution = {k: v / total_cat for k, v in cat_counter.most_common()}
    top_categories = [k for k, _ in cat_counter.most_common(5)]

    # Category distribution vector (padded to NUM_CATEGORY_SLOTS)
    cat_values = [v / total_cat for _, v in cat_counter.most_common(NUM_CATEGORY_SLOTS)]
    cat_vector = np.zeros(NUM_CATEGORY_SLOTS)
    cat_vector[:len(cat_values)] = cat_values

    return {
        'customer_id': customer_id,
        'recency_days': recency_days,
        'frequency': frequency,
        'monetary': monetary,
        'avg_order_value': avg_order_value,
        'max_order_value': max_order_value,
        'min_order_value': min_order_value,
        'total_items_purchased': total_items,
        'unique_products': unique_products,
        'unique_categories': unique_categories,
        'avg_items_per_order': avg_items,
        'cancelled_ratio': cancelled_ratio,
        'days_as_customer': days_as_customer,
        'order_frequency_monthly': order_freq_monthly,
        'preferred_hour': preferred_hour,
        'preferred_hour_sin': hour_sin,
        'preferred_hour_cos': hour_cos,
        'preferred_dow': preferred_dow,
        'preferred_dow_sin': dow_sin,
        'preferred_dow_cos': dow_cos,
        'weekend_ratio': weekend_ratio,
        'hour_distribution': hour_dist.tolist(),
        'dow_distribution': dow_dist.tolist(),
        'category_distribution': category_distribution,
        'category_vector': cat_vector.tolist(),
        'top_categories': top_categories,
    }


def features_to_vector(features):
    """
    Convert a feature dictionary into a flat numpy array for model input.

    Returns:
        numpy array of shape (TOTAL_FEATURE_DIM,)
    """
    static = [
        features['recency_days'],
        features['frequency'],
        features['monetary'],
        features['avg_order_value'],
        features['max_order_value'],
        features['min_order_value'],
        features['total_items_purchased'],
        features['unique_products'],
        features['unique_categories'],
        features['avg_items_per_order'],
        features['cancelled_ratio'],
        features['days_as_customer'],
        features['order_frequency_monthly'],
        features['preferred_hour_sin'],
        features['preferred_hour_cos'],
        features['preferred_dow_sin'],
        features['preferred_dow_cos'],
        features['weekend_ratio'],
    ]

    category = features.get('category_vector', [0] * NUM_CATEGORY_SLOTS)
    hour_dist = features.get('hour_distribution', [0] * 24)
    dow_dist = features.get('dow_distribution', [0] * 7)

    vec = np.array(static + list(category) + list(hour_dist) + list(dow_dist),
                   dtype=np.float32)
    return vec


def normalize_features(feature_matrix):
    """
    Z-score normalization on a feature matrix.

    Args:
        feature_matrix: numpy array of shape (num_customers, TOTAL_FEATURE_DIM)

    Returns:
        normalized matrix, mean vector, std vector
    """
    mean = feature_matrix.mean(axis=0)
    std = feature_matrix.std(axis=0)
    std[std == 0] = 1.0  # avoid division by zero
    normalized = (feature_matrix - mean) / std
    return normalized, mean, std


def build_purchase_sequences(events_by_customer, max_seq_len=50,
                              category_to_idx=None):
    """
    Build purchase sequences from events for the LSTM model.

    Args:
        events_by_customer: dict mapping customer_id → list of events
        max_seq_len: maximum sequence length (truncate/pad)
        category_to_idx: dict mapping category name → index

    Returns:
        category_sequences: (num_customers, max_seq_len) int array
        amount_sequences: (num_customers, max_seq_len) float array
        time_delta_sequences: (num_customers, max_seq_len) float array
        targets: (num_customers,) int array - next category index
        customer_ids: list of customer IDs
    """
    if category_to_idx is None:
        all_cats = set()
        for evts in events_by_customer.values():
            for e in evts:
                if e['event_type'] == 'purchase':
                    all_cats.add(e.get('category_name', 'Unknown'))
        category_to_idx = {cat: idx + 1 for idx, cat in enumerate(sorted(all_cats))}

    category_seqs = []
    amount_seqs = []
    time_delta_seqs = []
    targets = []
    customer_ids = []

    max_amount = 1.0  # will normalize later

    for cust_id, events in events_by_customer.items():
        purchases = sorted(
            [e for e in events if e['event_type'] == 'purchase'],
            key=lambda e: e['timestamp']
        )

        if len(purchases) < 2:
            continue

        # Use all but last as sequence, last as target
        seq_events = purchases[:-1]
        target_event = purchases[-1]

        cat_seq = []
        amt_seq = []
        td_seq = []

        prev_time = seq_events[0]['timestamp']
        for e in seq_events:
            cat_idx = category_to_idx.get(e.get('category_name', 'Unknown'), 0)
            cat_seq.append(cat_idx)
            amt_seq.append(float(e['amount']))
            td = (e['timestamp'] - prev_time).total_seconds() / 86400.0  # days
            td_seq.append(td)
            prev_time = e['timestamp']

        # Truncate or pad
        if len(cat_seq) > max_seq_len:
            cat_seq = cat_seq[-max_seq_len:]
            amt_seq = amt_seq[-max_seq_len:]
            td_seq = td_seq[-max_seq_len:]
        else:
            pad_len = max_seq_len - len(cat_seq)
            cat_seq = [0] * pad_len + cat_seq
            amt_seq = [0.0] * pad_len + amt_seq
            td_seq = [0.0] * pad_len + td_seq

        target_cat = category_to_idx.get(
            target_event.get('category_name', 'Unknown'), 0)

        category_seqs.append(cat_seq)
        amount_seqs.append(amt_seq)
        time_delta_seqs.append(td_seq)
        targets.append(target_cat)
        customer_ids.append(cust_id)

        max_amount = max(max_amount, max(amt_seq))

    if not category_seqs:
        return (np.array([]), np.array([]), np.array([]),
                np.array([]), [], category_to_idx)

    category_seqs = np.array(category_seqs, dtype=np.int64)
    amount_seqs = np.array(amount_seqs, dtype=np.float32) / max_amount
    time_delta_seqs = np.array(time_delta_seqs, dtype=np.float32)
    # Normalize time deltas
    td_max = time_delta_seqs.max()
    if td_max > 0:
        time_delta_seqs = time_delta_seqs / td_max
    targets = np.array(targets, dtype=np.int64)

    return (category_seqs, amount_seqs, time_delta_seqs,
            targets, customer_ids, category_to_idx)


def _empty_features(customer_id):
    """Return an empty feature dict for a customer with no purchases."""
    return {
        'customer_id': customer_id,
        'recency_days': 999,
        'frequency': 0,
        'monetary': 0,
        'avg_order_value': 0,
        'max_order_value': 0,
        'min_order_value': 0,
        'total_items_purchased': 0,
        'unique_products': 0,
        'unique_categories': 0,
        'avg_items_per_order': 0,
        'cancelled_ratio': 0,
        'days_as_customer': 0,
        'order_frequency_monthly': 0,
        'preferred_hour': 0,
        'preferred_hour_sin': 0,
        'preferred_hour_cos': 1.0,
        'preferred_dow': 0,
        'preferred_dow_sin': 0,
        'preferred_dow_cos': 1.0,
        'weekend_ratio': 0,
        'hour_distribution': [0] * 24,
        'dow_distribution': [0] * 7,
        'category_distribution': {},
        'category_vector': [0] * NUM_CATEGORY_SLOTS,
        'top_categories': [],
    }
