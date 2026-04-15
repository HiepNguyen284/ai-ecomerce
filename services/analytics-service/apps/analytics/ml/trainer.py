Sua"""
Model Training Pipeline for Customer Behavior Analysis.

Handles training all four deep learning models:
1. Autoencoder → customer embeddings
2. Churn prediction network
3. CLV prediction network
4. Purchase sequence LSTM

Also includes K-Means clustering on learned embeddings for segmentation.
"""

import os
import json
import time
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.cluster import KMeans
from django.conf import settings
from django.utils import timezone

from .deep_models import (
    CustomerBehaviorAutoencoder,
    ChurnPredictionNetwork,
    CLVPredictionNetwork,
    PurchaseSequenceModel,
)
from .features import (
    TOTAL_FEATURE_DIM,
    normalize_features,
    features_to_vector,
    build_purchase_sequences,
    extract_customer_features,
)

logger = logging.getLogger(__name__)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Default hyperparameters
DEFAULT_CONFIG = {
    'autoencoder': {
        'embedding_dim': 32,
        'epochs': 100,
        'batch_size': 64,
        'lr': 1e-3,
        'weight_decay': 1e-5,
    },
    'churn': {
        'epochs': 80,
        'batch_size': 64,
        'lr': 5e-4,
        'weight_decay': 1e-4,
    },
    'clv': {
        'epochs': 100,
        'batch_size': 64,
        'lr': 5e-4,
        'weight_decay': 1e-4,
    },
    'sequence': {
        'epochs': 60,
        'batch_size': 32,
        'lr': 1e-3,
        'max_seq_len': 50,
    },
    'clustering': {
        'n_clusters': 5,
    },
}


class TrainingPipeline:
    """
    End-to-end training pipeline for all customer behavior models.
    """

    def __init__(self, config=None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.models_dir = getattr(settings, 'ML_MODELS_DIR',
                                  os.path.join(settings.BASE_DIR, 'ml_models'))
        os.makedirs(self.models_dir, exist_ok=True)

        self.autoencoder = None
        self.churn_model = None
        self.clv_model = None
        self.sequence_model = None
        self.kmeans = None
        self.feature_mean = None
        self.feature_std = None
        self.category_to_idx = None
        self.segment_definitions = None

    def train_all(self, events_by_customer, churn_labels=None,
                  clv_labels=None, category_to_idx=None):
        """
        Train all models end-to-end.

        Args:
            events_by_customer: dict mapping customer_id → list of event dicts
            churn_labels: dict mapping customer_id → 0/1
            clv_labels: dict mapping customer_id → float CLV value
            category_to_idx: dict mapping category name → int index

        Returns:
            dict with training metrics for all models
        """
        logger.info(f"Starting training pipeline with {len(events_by_customer)} customers")
        results = {}
        reference_date = timezone.now()

        # Step 1: Extract features for all customers
        logger.info("Step 1/6: Extracting features...")
        feature_dicts = {}
        for cust_id, events in events_by_customer.items():
            events_as_dicts = []
            for e in events:
                events_as_dicts.append({
                    'event_type': e['event_type'],
                    'amount': e.get('amount', 0),
                    'quantity': e.get('quantity', 1),
                    'timestamp': e['timestamp'],
                    'product_id': e.get('product_id'),
                    'product_name': e.get('product_name', ''),
                    'category_name': e.get('category_name', 'Unknown'),
                })
            features = extract_customer_features(events_as_dicts, cust_id,
                                                  reference_date)
            feature_dicts[cust_id] = features

        customer_ids = list(feature_dicts.keys())
        feature_matrix = np.array([features_to_vector(feature_dicts[cid])
                                   for cid in customer_ids])

        # Normalize
        feature_matrix_norm, self.feature_mean, self.feature_std = \
            normalize_features(feature_matrix)

        logger.info(f"  Feature matrix shape: {feature_matrix_norm.shape}")

        # Step 2: Train autoencoder
        logger.info("Step 2/6: Training autoencoder...")
        ae_metrics = self._train_autoencoder(feature_matrix_norm)
        results['autoencoder'] = ae_metrics

        # Step 3: Extract embeddings and cluster
        logger.info("Step 3/6: Clustering embeddings...")
        embeddings = self._get_embeddings(feature_matrix_norm)
        cluster_metrics = self._cluster_embeddings(
            embeddings, customer_ids, feature_dicts)
        results['clustering'] = cluster_metrics

        # Step 4: Train churn model
        logger.info("Step 4/6: Training churn prediction model...")
        if churn_labels:
            churn_metrics = self._train_churn_model(
                feature_matrix_norm, customer_ids, churn_labels)
        else:
            # Generate pseudo-labels from features
            churn_metrics = self._train_churn_model_unsupervised(
                feature_matrix_norm, feature_dicts, customer_ids)
        results['churn'] = churn_metrics

        # Step 5: Train CLV model
        logger.info("Step 5/6: Training CLV prediction model...")
        if clv_labels:
            clv_metrics = self._train_clv_model(
                feature_matrix_norm, customer_ids, clv_labels)
        else:
            clv_metrics = self._train_clv_model_unsupervised(
                feature_matrix_norm, feature_dicts, customer_ids)
        results['clv'] = clv_metrics

        # Step 6: Train sequence model
        logger.info("Step 6/6: Training sequence prediction model...")
        seq_metrics = self._train_sequence_model(
            events_by_customer, category_to_idx)
        results['sequence'] = seq_metrics

        # Save all models and metadata
        self._save_all(customer_ids, feature_dicts, embeddings)

        logger.info("Training pipeline complete!")
        return results

    def _train_autoencoder(self, feature_matrix):
        """Train the autoencoder on the normalized feature matrix."""
        cfg = self.config['autoencoder']
        input_dim = feature_matrix.shape[1]

        self.autoencoder = CustomerBehaviorAutoencoder(
            input_dim=input_dim,
            embedding_dim=cfg['embedding_dim'],
        ).to(DEVICE)

        dataset = TensorDataset(
            torch.FloatTensor(feature_matrix).to(DEVICE))
        loader = DataLoader(dataset, batch_size=cfg['batch_size'], shuffle=True)

        optimizer = optim.Adam(self.autoencoder.parameters(),
                               lr=cfg['lr'], weight_decay=cfg['weight_decay'])
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=cfg['epochs'])
        criterion = nn.MSELoss()

        start_time = time.time()
        losses = []

        self.autoencoder.train()
        for epoch in range(cfg['epochs']):
            epoch_loss = 0
            for (batch_x,) in loader:
                optimizer.zero_grad()
                reconstructed, _ = self.autoencoder(batch_x)
                loss = criterion(reconstructed, batch_x)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg_loss = epoch_loss / len(loader)
            losses.append(avg_loss)
            scheduler.step()

            if (epoch + 1) % 20 == 0:
                logger.info(f"  Autoencoder epoch {epoch+1}/{cfg['epochs']}, "
                            f"loss: {avg_loss:.6f}")

        duration = time.time() - start_time
        return {
            'final_loss': losses[-1],
            'epochs': cfg['epochs'],
            'duration': duration,
            'loss_history': losses,
        }

    def _get_embeddings(self, feature_matrix):
        """Get embeddings from trained autoencoder."""
        self.autoencoder.eval()
        with torch.no_grad():
            x = torch.FloatTensor(feature_matrix).to(DEVICE)
            embeddings = self.autoencoder.encode(x).cpu().numpy()
        return embeddings

    def _cluster_embeddings(self, embeddings, customer_ids, feature_dicts):
        """Cluster customer embeddings using K-Means."""
        n_clusters = self.config['clustering']['n_clusters']
        n_clusters = min(n_clusters, len(embeddings))

        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(embeddings)

        # Analyze clusters to give them meaningful names
        cluster_stats = {}
        for i in range(n_clusters):
            mask = labels == i
            cluster_cids = [customer_ids[j] for j in range(len(labels)) if mask[j]]
            cluster_features = [feature_dicts[cid] for cid in cluster_cids]

            avg_monetary = np.mean([f['monetary'] for f in cluster_features])
            avg_frequency = np.mean([f['frequency'] for f in cluster_features])
            avg_recency = np.mean([f['recency_days'] for f in cluster_features])
            avg_aov = np.mean([f['avg_order_value'] for f in cluster_features])

            cluster_stats[i] = {
                'count': int(mask.sum()),
                'avg_monetary': float(avg_monetary),
                'avg_frequency': float(avg_frequency),
                'avg_recency': float(avg_recency),
                'avg_aov': float(avg_aov),
                'centroid': self.kmeans.cluster_centers_[i].tolist(),
            }

        # Auto-name segments based on characteristics
        self.segment_definitions = self._auto_name_segments(cluster_stats)

        return {
            'n_clusters': n_clusters,
            'inertia': float(self.kmeans.inertia_),
            'cluster_stats': cluster_stats,
            'segment_definitions': self.segment_definitions,
        }

    def _auto_name_segments(self, cluster_stats):
        """Automatically assign meaningful names to segments."""
        segments = []
        sorted_clusters = sorted(cluster_stats.items(),
                                  key=lambda x: x[1]['avg_monetary'], reverse=True)

        name_templates = [
            {
                'name': 'VIP Champions',
                'name_vi': 'Khách VIP Hạng Nhất',
                'description': 'Highest spenders with frequent purchases',
                'description_vi': 'Khách hàng chi tiêu cao nhất với tần suất mua sắm thường xuyên',
                'color': '#f59e0b',
                'icon': 'crown',
            },
            {
                'name': 'Loyal Customers',
                'name_vi': 'Khách Hàng Trung Thành',
                'description': 'Regular buyers with good spending habits',
                'description_vi': 'Khách hàng mua sắm đều đặn với thói quen chi tiêu tốt',
                'color': '#10b981',
                'icon': 'heart',
            },
            {
                'name': 'Potential Growers',
                'name_vi': 'Khách Hàng Tiềm Năng',
                'description': 'Moderate activity with growth potential',
                'description_vi': 'Hoạt động trung bình nhưng có tiềm năng phát triển',
                'color': '#6366f1',
                'icon': 'trending-up',
            },
            {
                'name': 'At Risk',
                'name_vi': 'Khách Hàng Có Nguy Cơ',
                'description': 'Declining activity, may churn soon',
                'description_vi': 'Hoạt động giảm dần, có nguy cơ rời bỏ',
                'color': '#f97316',
                'icon': 'alert-triangle',
            },
            {
                'name': 'Hibernating',
                'name_vi': 'Khách Hàng Ngủ Đông',
                'description': 'Low activity and spending',
                'description_vi': 'Hoạt động và chi tiêu thấp',
                'color': '#64748b',
                'icon': 'moon',
            },
        ]

        for idx, (cluster_id, stats) in enumerate(sorted_clusters):
            template = name_templates[min(idx, len(name_templates) - 1)]
            segments.append({
                'segment_id': int(cluster_id),
                **template,
                'customer_count': stats['count'],
                'avg_monetary': stats['avg_monetary'],
                'avg_frequency': stats['avg_frequency'],
                'avg_recency': stats['avg_recency'],
                'centroid': stats['centroid'],
            })

        return segments

    def _train_churn_model_unsupervised(self, feature_matrix, feature_dicts,
                                         customer_ids):
        """
        Train churn model with pseudo-labels derived from behavioral signals.
        Customers with high recency and low frequency are labeled as churned.
        """
        # Generate pseudo-labels
        labels = []
        for cid in customer_ids:
            f = feature_dicts[cid]
            # Heuristic: high recency + low frequency → churn
            recency_score = min(f['recency_days'] / 90.0, 1.0)
            freq_score = 1 - min(f['frequency'] / 10.0, 1.0)
            churn_score = 0.6 * recency_score + 0.4 * freq_score
            labels.append(1.0 if churn_score > 0.5 else 0.0)

        return self._train_churn_model(feature_matrix, customer_ids,
                                        dict(zip(customer_ids, labels)))

    def _train_churn_model(self, feature_matrix, customer_ids, churn_labels):
        """Train the churn prediction network."""
        cfg = self.config['churn']
        input_dim = feature_matrix.shape[1]

        self.churn_model = ChurnPredictionNetwork(input_dim).to(DEVICE)

        y = np.array([churn_labels.get(cid, 0) for cid in customer_ids],
                     dtype=np.float32)

        dataset = TensorDataset(
            torch.FloatTensor(feature_matrix).to(DEVICE),
            torch.FloatTensor(y).unsqueeze(1).to(DEVICE),
        )
        loader = DataLoader(dataset, batch_size=cfg['batch_size'], shuffle=True)

        optimizer = optim.Adam(self.churn_model.parameters(),
                               lr=cfg['lr'], weight_decay=cfg['weight_decay'])
        criterion = nn.BCELoss()

        start_time = time.time()
        losses = []

        self.churn_model.train()
        for epoch in range(cfg['epochs']):
            epoch_loss = 0
            correct = 0
            total = 0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                pred = self.churn_model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                correct += ((pred > 0.5).float() == batch_y).sum().item()
                total += batch_y.size(0)

            avg_loss = epoch_loss / len(loader)
            accuracy = correct / total if total > 0 else 0
            losses.append(avg_loss)

            if (epoch + 1) % 20 == 0:
                logger.info(f"  Churn epoch {epoch+1}/{cfg['epochs']}, "
                            f"loss: {avg_loss:.6f}, acc: {accuracy:.4f}")

        duration = time.time() - start_time
        return {
            'final_loss': losses[-1],
            'accuracy': accuracy,
            'epochs': cfg['epochs'],
            'duration': duration,
            'churn_rate': float(y.mean()),
        }

    def _train_clv_model_unsupervised(self, feature_matrix, feature_dicts,
                                       customer_ids):
        """
        Train CLV model with pseudo-labels derived from monetary value and
        projected future behavior.
        """
        labels = {}
        for cid in customer_ids:
            f = feature_dicts[cid]
            # Simple CLV estimation: monetary * frequency factor * retention factor
            freq_factor = 1 + min(f['order_frequency_monthly'], 5) * 0.3
            retention = max(0, 1 - f.get('cancelled_ratio', 0))
            clv = float(f['monetary']) * freq_factor * retention
            labels[cid] = clv

        return self._train_clv_model(feature_matrix, customer_ids, labels)

    def _train_clv_model(self, feature_matrix, customer_ids, clv_labels):
        """Train the CLV regression network."""
        cfg = self.config['clv']
        input_dim = feature_matrix.shape[1]

        self.clv_model = CLVPredictionNetwork(input_dim).to(DEVICE)

        y = np.array([clv_labels.get(cid, 0) for cid in customer_ids],
                     dtype=np.float32)
        # Normalize CLV targets
        y_mean = y.mean()
        y_std = y.std()
        if y_std == 0:
            y_std = 1.0
        y_norm = (y - y_mean) / y_std

        dataset = TensorDataset(
            torch.FloatTensor(feature_matrix).to(DEVICE),
            torch.FloatTensor(y_norm).unsqueeze(1).to(DEVICE),
        )
        loader = DataLoader(dataset, batch_size=cfg['batch_size'], shuffle=True)

        optimizer = optim.Adam(self.clv_model.parameters(),
                               lr=cfg['lr'], weight_decay=cfg['weight_decay'])
        criterion = nn.MSELoss()

        start_time = time.time()
        losses = []

        self.clv_model.train()
        for epoch in range(cfg['epochs']):
            epoch_loss = 0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                pred = self.clv_model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg_loss = epoch_loss / len(loader)
            losses.append(avg_loss)

            if (epoch + 1) % 20 == 0:
                logger.info(f"  CLV epoch {epoch+1}/{cfg['epochs']}, "
                            f"loss: {avg_loss:.6f}")

        duration = time.time() - start_time

        # Save CLV normalization params
        self.clv_mean = float(y_mean)
        self.clv_std = float(y_std)

        return {
            'final_loss': losses[-1],
            'epochs': cfg['epochs'],
            'duration': duration,
            'clv_mean': self.clv_mean,
            'clv_std': self.clv_std,
        }

    def _train_sequence_model(self, events_by_customer, category_to_idx=None):
        """Train the LSTM sequence prediction model."""
        cfg = self.config['sequence']

        # Build sequences
        (cat_seqs, amt_seqs, td_seqs, targets,
         cust_ids, cat_idx) = build_purchase_sequences(
            events_by_customer,
            max_seq_len=cfg['max_seq_len'],
            category_to_idx=category_to_idx,
        )

        self.category_to_idx = cat_idx

        if len(cat_seqs) == 0:
            logger.warning("  No sequences available for training!")
            return {'final_loss': 0, 'accuracy': 0, 'epochs': 0, 'duration': 0}

        num_categories = max(cat_idx.values()) + 1
        self.sequence_model = PurchaseSequenceModel(
            num_categories=num_categories,
        ).to(DEVICE)

        dataset = TensorDataset(
            torch.LongTensor(cat_seqs).to(DEVICE),
            torch.FloatTensor(amt_seqs).to(DEVICE),
            torch.FloatTensor(td_seqs).to(DEVICE),
            torch.LongTensor(targets).to(DEVICE),
        )
        loader = DataLoader(dataset, batch_size=cfg['batch_size'], shuffle=True)

        optimizer = optim.Adam(self.sequence_model.parameters(), lr=cfg['lr'])
        criterion = nn.CrossEntropyLoss()

        start_time = time.time()
        losses = []

        self.sequence_model.train()
        for epoch in range(cfg['epochs']):
            epoch_loss = 0
            correct = 0
            total = 0
            for batch_cat, batch_amt, batch_td, batch_target in loader:
                optimizer.zero_grad()
                logits = self.sequence_model(batch_cat, batch_amt, batch_td)
                loss = criterion(logits, batch_target)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

                preds = logits.argmax(dim=1)
                correct += (preds == batch_target).sum().item()
                total += batch_target.size(0)

            avg_loss = epoch_loss / len(loader)
            accuracy = correct / total if total > 0 else 0
            losses.append(avg_loss)

            if (epoch + 1) % 15 == 0:
                logger.info(f"  Sequence epoch {epoch+1}/{cfg['epochs']}, "
                            f"loss: {avg_loss:.6f}, acc: {accuracy:.4f}")

        duration = time.time() - start_time
        return {
            'final_loss': losses[-1],
            'accuracy': accuracy,
            'epochs': cfg['epochs'],
            'duration': duration,
            'num_categories': num_categories,
            'num_sequences': len(cat_seqs),
        }

    def _save_all(self, customer_ids, feature_dicts, embeddings):
        """Save all trained models, metadata, and normalization parameters."""
        # Save PyTorch models
        if self.autoencoder:
            torch.save(self.autoencoder.state_dict(),
                       os.path.join(self.models_dir, 'autoencoder.pt'))

        if self.churn_model:
            torch.save(self.churn_model.state_dict(),
                       os.path.join(self.models_dir, 'churn_model.pt'))

        if self.clv_model:
            torch.save(self.clv_model.state_dict(),
                       os.path.join(self.models_dir, 'clv_model.pt'))

        if self.sequence_model:
            torch.save(self.sequence_model.state_dict(),
                       os.path.join(self.models_dir, 'sequence_model.pt'))

        # Save metadata
        metadata = {
            'feature_dim': TOTAL_FEATURE_DIM,
            'embedding_dim': self.config['autoencoder']['embedding_dim'],
            'feature_mean': self.feature_mean.tolist() if self.feature_mean is not None else [],
            'feature_std': self.feature_std.tolist() if self.feature_std is not None else [],
            'category_to_idx': self.category_to_idx or {},
            'clv_mean': getattr(self, 'clv_mean', 0),
            'clv_std': getattr(self, 'clv_std', 1),
            'n_clusters': self.config['clustering']['n_clusters'],
            'segment_definitions': self.segment_definitions or [],
            'trained_at': timezone.now().isoformat(),
        }
        with open(os.path.join(self.models_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save KMeans
        if self.kmeans is not None:
            import pickle
            with open(os.path.join(self.models_dir, 'kmeans.pkl'), 'wb') as f:
                pickle.dump(self.kmeans, f)

        logger.info(f"All models saved to {self.models_dir}")
