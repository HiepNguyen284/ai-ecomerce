"""
Inference / Prediction Module for Customer Behavior Analysis.

Loads trained models and provides prediction methods for:
- Customer embedding extraction
- Segment assignment
- Churn risk scoring
- CLV prediction
- Next purchase category prediction
"""

import os
import json
import pickle
import logging
import numpy as np
import torch
from django.conf import settings

from .deep_models import (
    CustomerBehaviorAutoencoder,
    ChurnPredictionNetwork,
    CLVPredictionNetwork,
    PurchaseSequenceModel,
)
from .features import (
    TOTAL_FEATURE_DIM,
    features_to_vector,
    extract_customer_features,
)

logger = logging.getLogger(__name__)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class BehaviorPredictor:
    """
    Loads trained models and performs inference for customer behavior analysis.
    """

    def __init__(self):
        self.models_dir = getattr(settings, 'ML_MODELS_DIR',
                                  os.path.join(settings.BASE_DIR, 'ml_models'))
        self.autoencoder = None
        self.churn_model = None
        self.clv_model = None
        self.sequence_model = None
        self.kmeans = None
        self.metadata = None
        self._loaded = False

    def load(self):
        """Load all trained models and metadata."""
        metadata_path = os.path.join(self.models_dir, 'metadata.json')
        if not os.path.exists(metadata_path):
            logger.warning("No trained models found. Run training first.")
            return False

        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)

        feature_dim = self.metadata.get('feature_dim', TOTAL_FEATURE_DIM)
        embedding_dim = self.metadata.get('embedding_dim', 32)

        # Load autoencoder
        ae_path = os.path.join(self.models_dir, 'autoencoder.pt')
        if os.path.exists(ae_path):
            self.autoencoder = CustomerBehaviorAutoencoder(
                input_dim=feature_dim,
                embedding_dim=embedding_dim,
            ).to(DEVICE)
            self.autoencoder.load_state_dict(
                torch.load(ae_path, map_location=DEVICE, weights_only=True))
            self.autoencoder.eval()
            logger.info("Loaded autoencoder model")

        # Load churn model
        churn_path = os.path.join(self.models_dir, 'churn_model.pt')
        if os.path.exists(churn_path):
            self.churn_model = ChurnPredictionNetwork(feature_dim).to(DEVICE)
            self.churn_model.load_state_dict(
                torch.load(churn_path, map_location=DEVICE, weights_only=True))
            self.churn_model.eval()
            logger.info("Loaded churn prediction model")

        # Load CLV model
        clv_path = os.path.join(self.models_dir, 'clv_model.pt')
        if os.path.exists(clv_path):
            self.clv_model = CLVPredictionNetwork(feature_dim).to(DEVICE)
            self.clv_model.load_state_dict(
                torch.load(clv_path, map_location=DEVICE, weights_only=True))
            self.clv_model.eval()
            logger.info("Loaded CLV prediction model")

        # Load sequence model
        seq_path = os.path.join(self.models_dir, 'sequence_model.pt')
        cat_to_idx = self.metadata.get('category_to_idx', {})
        if os.path.exists(seq_path) and cat_to_idx:
            num_categories = max(cat_to_idx.values()) + 1
            self.sequence_model = PurchaseSequenceModel(
                num_categories=num_categories,
            ).to(DEVICE)
            self.sequence_model.load_state_dict(
                torch.load(seq_path, map_location=DEVICE, weights_only=True))
            self.sequence_model.eval()
            logger.info("Loaded sequence prediction model")

        # Load KMeans
        kmeans_path = os.path.join(self.models_dir, 'kmeans.pkl')
        if os.path.exists(kmeans_path):
            with open(kmeans_path, 'rb') as f:
                self.kmeans = pickle.load(f)
            logger.info("Loaded KMeans model")

        self._loaded = True
        return True

    def ensure_loaded(self):
        """Ensure models are loaded, loading them if needed."""
        if not self._loaded:
            return self.load()
        return True

    def _normalize(self, feature_vector):
        """Apply saved normalization to a feature vector."""
        mean = np.array(self.metadata.get('feature_mean', []))
        std = np.array(self.metadata.get('feature_std', []))
        if len(mean) == 0 or len(std) == 0:
            return feature_vector
        std[std == 0] = 1.0
        return (feature_vector - mean) / std

    def predict_customer(self, events, customer_id, reference_date=None):
        """
        Run all predictions for a single customer.

        Args:
            events: list of event dicts for this customer
            customer_id: the customer's UUID
            reference_date: datetime for recency computation

        Returns:
            dict with all predictions and features
        """
        if not self.ensure_loaded():
            return None

        # Extract features
        events_as_dicts = []
        for e in events:
            events_as_dicts.append({
                'event_type': e.get('event_type', 'purchase'),
                'amount': e.get('amount', 0),
                'quantity': e.get('quantity', 1),
                'timestamp': e.get('timestamp'),
                'product_id': e.get('product_id'),
                'product_name': e.get('product_name', ''),
                'category_name': e.get('category_name', 'Unknown'),
            })

        features = extract_customer_features(events_as_dicts, customer_id,
                                              reference_date)
        feature_vec = features_to_vector(features)
        feature_norm = self._normalize(feature_vec)

        result = {
            'customer_id': str(customer_id),
            'features': features,
        }

        x = torch.FloatTensor(feature_norm).unsqueeze(0).to(DEVICE)

        # Embedding
        if self.autoencoder:
            with torch.no_grad():
                embedding = self.autoencoder.encode(x).cpu().numpy()[0]
            result['embedding'] = embedding.tolist()

            # Segment assignment
            if self.kmeans is not None:
                segment_id = int(self.kmeans.predict(embedding.reshape(1, -1))[0])
                segment_defs = self.metadata.get('segment_definitions', [])
                segment_info = next(
                    (s for s in segment_defs if s['segment_id'] == segment_id),
                    {'name': f'Segment {segment_id}', 'name_vi': f'Phân khúc {segment_id}'}
                )
                result['segment_id'] = segment_id
                result['segment_name'] = segment_info.get('name', '')
                result['segment_name_vi'] = segment_info.get('name_vi', '')
                result['segment_color'] = segment_info.get('color', '#6366f1')

        # Churn risk
        if self.churn_model:
            with torch.no_grad():
                churn_risk = self.churn_model(x).cpu().item()
            result['churn_risk'] = round(churn_risk, 4)
            result['churn_label'] = (
                'Cao' if churn_risk > 0.7 else
                'Trung bình' if churn_risk > 0.3 else 'Thấp'
            )

        # CLV
        if self.clv_model:
            with torch.no_grad():
                clv_norm = self.clv_model(x).cpu().item()
            clv_mean = self.metadata.get('clv_mean', 0)
            clv_std = self.metadata.get('clv_std', 1)
            clv = max(0, clv_norm * clv_std + clv_mean)
            result['predicted_clv'] = round(clv, 2)

        # Next purchase prediction
        if self.sequence_model and events_as_dicts:
            next_cats = self._predict_next_purchase(events_as_dicts)
            result['next_purchase_predictions'] = next_cats

        return result

    def _predict_next_purchase(self, events, top_k=5):
        """Predict top-k next purchase categories."""
        cat_to_idx = self.metadata.get('category_to_idx', {})
        idx_to_cat = {v: k for k, v in cat_to_idx.items()}

        purchases = sorted(
            [e for e in events if e.get('event_type') == 'purchase'],
            key=lambda e: e['timestamp']
        )

        if len(purchases) < 1:
            return []

        max_seq_len = 50
        cat_seq = []
        amt_seq = []
        td_seq = []

        max_amount = max(float(e.get('amount', 1)) for e in purchases) or 1.0

        prev_time = purchases[0]['timestamp']
        for e in purchases[-max_seq_len:]:
            cat_idx = cat_to_idx.get(e.get('category_name', 'Unknown'), 0)
            cat_seq.append(cat_idx)
            amt_seq.append(float(e.get('amount', 0)) / max_amount)
            td = (e['timestamp'] - prev_time).total_seconds() / 86400.0
            td_seq.append(min(td / 30.0, 1.0))
            prev_time = e['timestamp']

        # Pad
        pad_len = max_seq_len - len(cat_seq)
        cat_seq = [0] * pad_len + cat_seq
        amt_seq = [0.0] * pad_len + amt_seq
        td_seq = [0.0] * pad_len + td_seq

        cat_t = torch.LongTensor([cat_seq]).to(DEVICE)
        amt_t = torch.FloatTensor([amt_seq]).to(DEVICE)
        td_t = torch.FloatTensor([td_seq]).to(DEVICE)

        with torch.no_grad():
            logits = self.sequence_model(cat_t, amt_t, td_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        top_indices = probs.argsort()[-top_k:][::-1]
        results = []
        for idx in top_indices:
            cat_name = idx_to_cat.get(int(idx), f'Category {idx}')
            results.append({
                'category': cat_name,
                'confidence': round(float(probs[idx]), 4),
            })

        return results

    def predict_batch(self, events_by_customer, reference_date=None):
        """
        Run predictions for multiple customers.

        Args:
            events_by_customer: dict mapping customer_id → list of events

        Returns:
            dict mapping customer_id → prediction results
        """
        results = {}
        for cust_id, events in events_by_customer.items():
            try:
                result = self.predict_customer(events, cust_id, reference_date)
                if result:
                    results[cust_id] = result
            except Exception as e:
                logger.error(f"Error predicting for customer {cust_id}: {e}")
        return results


# Singleton instance
_predictor = None


def get_predictor():
    """Get or create the singleton BehaviorPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = BehaviorPredictor()
    return _predictor
