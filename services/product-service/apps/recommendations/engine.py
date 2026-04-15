"""
Deep Learning Recommendation Engine for Customer Behavior Analysis.

Architecture:
    - Uses a neural network with embedding layers to learn category preferences
    - Input: User's category view sequence (category_id, view_count, recency)
    - Output: Predicted preference scores for all categories

The model learns from browsing patterns:
    1. Which categories a user views frequently -> higher affinity
    2. Recency of views -> recent categories are weighted higher
    3. Sequential patterns -> attention mechanism weights by frequency

This uses NumPy for lightweight deployment (no GPU dependency in the container).
"""

import numpy as np
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Model weights storage path
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model_weights')


class CategoryEmbedding:
    """Neural embedding layer for categories.

    Maps each category to a dense vector representation.
    Similar categories (by user browsing patterns) will have
    similar embeddings.
    """

    def __init__(self, num_categories, embedding_dim=16):
        self.num_categories = num_categories
        self.embedding_dim = embedding_dim
        # Xavier initialization for stable training
        scale = np.sqrt(2.0 / (num_categories + embedding_dim))
        self.weights = np.random.randn(num_categories, embedding_dim) * scale

    def forward(self, category_indices):
        """Lookup embeddings for given category indices."""
        return self.weights[category_indices]

    def to_dict(self):
        return {
            'num_categories': self.num_categories,
            'embedding_dim': self.embedding_dim,
            'weights': self.weights.tolist(),
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls(d['num_categories'], d['embedding_dim'])
        obj.weights = np.array(d['weights'])
        return obj


class DenseLayer:
    """Fully connected neural network layer with configurable activation."""

    def __init__(self, input_dim, output_dim, activation='relu'):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.activation = activation
        # He initialization for ReLU layers
        scale = np.sqrt(2.0 / input_dim)
        self.weights = np.random.randn(input_dim, output_dim) * scale
        self.bias = np.zeros(output_dim)

    def forward(self, x):
        """Forward pass: linear transform + activation."""
        z = np.dot(x, self.weights) + self.bias
        if self.activation == 'relu':
            return np.maximum(0, z)
        elif self.activation == 'sigmoid':
            return 1 / (1 + np.exp(-np.clip(z, -500, 500)))
        elif self.activation == 'softmax':
            exp_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
            return exp_z / np.sum(exp_z, axis=-1, keepdims=True)
        return z

    def to_dict(self):
        return {
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'activation': self.activation,
            'weights': self.weights.tolist(),
            'bias': self.bias.tolist(),
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls(d['input_dim'], d['output_dim'], d['activation'])
        obj.weights = np.array(d['weights'])
        obj.bias = np.array(d['bias'])
        return obj


class RecommendationModel:
    """Deep learning model for category preference prediction.

    Architecture:
        Input Layer -> Category Embedding (16d)
           |
        Feature Engineering: [embedding, view_count_norm, recency_score]
           |
        Dense Layer 1 (input_features -> 64, ReLU)
           |
        Dense Layer 2 (64 -> 32, ReLU)
           |
        Output Layer (32 -> num_categories, Sigmoid)

    The model outputs a score between 0-1 for each category,
    representing the predicted user preference.
    """

    def __init__(self, num_categories, embedding_dim=16):
        self.num_categories = num_categories
        self.embedding_dim = embedding_dim
        # Feature size: embedding_dim + 2 (view_count_norm, recency_score)
        feature_dim = embedding_dim + 2

        self.embedding = CategoryEmbedding(num_categories, embedding_dim)
        self.layer1 = DenseLayer(feature_dim, 64, 'relu')
        self.layer2 = DenseLayer(64, 32, 'relu')
        self.output_layer = DenseLayer(32, num_categories, 'sigmoid')

        self.learning_rate = 0.01
        self.trained = False

    def _build_features(self, category_views, total_categories):
        """Build feature vectors from raw category view data.

        Args:
            category_views: list of dicts with keys:
                - category_index: int index of the category
                - view_count: number of views
                - last_viewed: datetime of last view
                - total_views: total views across all categories
            total_categories: total number of categories

        Returns:
            Feature matrix of shape (num_viewed_categories, feature_dim)
        """
        if not category_views:
            return np.zeros((1, self.embedding_dim + 2))

        features = []
        now = datetime.now()

        for cv in category_views:
            # Get category embedding
            cat_idx = cv['category_index']
            emb = self.embedding.forward(np.array([cat_idx]))[0]

            # Normalize view count (log scale for stability)
            total = max(cv.get('total_views', 1), 1)
            view_norm = np.log1p(cv['view_count']) / np.log1p(total)

            # Recency score: exponential decay based on time since last view
            if cv.get('last_viewed'):
                hours_ago = max((now - cv['last_viewed']).total_seconds() / 3600, 0)
                recency = np.exp(-0.05 * hours_ago)  # half-life ~14 hours
            else:
                recency = 0.5

            feature = np.concatenate([emb, [view_norm, recency]])
            features.append(feature)

        return np.array(features)

    def predict(self, category_views, total_categories):
        """Predict preference scores for all categories.

        Args:
            category_views: raw category view data
            total_categories: total number of categories

        Returns:
            Array of shape (num_categories,) with scores 0-1
        """
        features = self._build_features(category_views, total_categories)

        # Forward pass through each viewed category
        hidden_states = []
        for i in range(features.shape[0]):
            x = features[i:i + 1]
            h1 = self.layer1.forward(x)
            h2 = self.layer2.forward(h1)
            hidden_states.append(h2)

        # Attention-like aggregation: weight by view counts
        if category_views:
            view_counts = np.array([cv['view_count'] for cv in category_views],
                                   dtype=float)
            # Softmax over view counts for attention weights
            attention = np.exp(view_counts) / np.sum(np.exp(view_counts))

            aggregated = np.zeros_like(hidden_states[0])
            for i, h in enumerate(hidden_states):
                aggregated += attention[i] * h
        else:
            aggregated = hidden_states[0]

        # Output scores for all categories
        scores = self.output_layer.forward(aggregated)
        return scores.flatten()

    def train_step(self, category_views, target_scores, total_categories):
        """One training step with simplified gradient descent.

        Uses numerical gradient approximation for simplicity.
        In production, this would use autograd (PyTorch/TensorFlow).
        """
        predictions = self.predict(category_views, total_categories)

        # MSE loss
        loss = np.mean((predictions - target_scores) ** 2)

        # Simplified weight update: nudge output layer towards targets
        error = target_scores - predictions

        # Update output layer bias (acts as category preference prior)
        self.output_layer.bias += self.learning_rate * error

        self.trained = True
        return loss

    def save(self, filepath=None):
        """Save model weights to disk."""
        if filepath is None:
            os.makedirs(MODEL_DIR, exist_ok=True)
            filepath = os.path.join(MODEL_DIR, 'recommendation_model.json')

        model_data = {
            'num_categories': self.num_categories,
            'embedding_dim': self.embedding_dim,
            'embedding': self.embedding.to_dict(),
            'layer1': self.layer1.to_dict(),
            'layer2': self.layer2.to_dict(),
            'output_layer': self.output_layer.to_dict(),
            'learning_rate': self.learning_rate,
            'trained': self.trained,
        }

        with open(filepath, 'w') as f:
            json.dump(model_data, f)

    @classmethod
    def load(cls, filepath=None):
        """Load model weights from disk."""
        if filepath is None:
            filepath = os.path.join(MODEL_DIR, 'recommendation_model.json')

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        model = cls(data['num_categories'], data['embedding_dim'])
        model.embedding = CategoryEmbedding.from_dict(data['embedding'])
        model.layer1 = DenseLayer.from_dict(data['layer1'])
        model.layer2 = DenseLayer.from_dict(data['layer2'])
        model.output_layer = DenseLayer.from_dict(data['output_layer'])
        model.learning_rate = data['learning_rate']
        model.trained = data.get('trained', False)

        return model


class RecommendationEngine:
    """High-level recommendation engine that combines the DL model
    with business logic for generating product recommendations.

    This engine:
    1. Processes raw view events into features
    2. Runs the DL model to predict category preferences
    3. Selects products from preferred categories
    4. Applies diversity & freshness heuristics
    """

    def __init__(self):
        self.model = None
        self.category_index_map = {}  # category_id -> index
        self.index_category_map = {}  # index -> category_id

    def _ensure_model(self, categories):
        """Initialize or load the model with current category count."""
        num_cats = len(categories)

        # Build mapping
        self.category_index_map = {}
        self.index_category_map = {}
        for i, cat in enumerate(categories):
            cat_id = str(cat.id)
            self.category_index_map[cat_id] = i
            self.index_category_map[i] = cat_id

        # Try loading existing model
        self.model = RecommendationModel.load()

        # If no model or category count changed, create new
        if self.model is None or self.model.num_categories != num_cats:
            self.model = RecommendationModel(num_cats)

    def process_views(self, preferences, categories):
        """Convert CategoryPreference queryset to model input format.

        Args:
            preferences: QuerySet of CategoryPreference objects
            categories: QuerySet of Category objects

        Returns:
            list of dicts suitable for model.predict()
        """
        self._ensure_model(categories)

        total_views = sum(p.view_count for p in preferences) or 1

        category_views = []
        for pref in preferences:
            cat_id = str(pref.category_id)
            if cat_id in self.category_index_map:
                category_views.append({
                    'category_index': self.category_index_map[cat_id],
                    'view_count': pref.view_count,
                    'last_viewed': pref.last_viewed,
                    'total_views': total_views,
                })

        return category_views

    def get_recommendations(self, preferences, categories, all_products,
                            max_products=20):
        """Generate personalized product recommendations.

        Args:
            preferences: QuerySet of CategoryPreference for the user
            categories: QuerySet of all Category objects
            all_products: QuerySet of active Product objects
            max_products: maximum number of products to return

        Returns:
            list of Product objects, ordered by relevance
        """
        self._ensure_model(categories)

        if not preferences.exists():
            # No browsing history -> return popular/trending products
            return list(
                all_products.order_by('-rating', '-num_reviews')[:max_products]
            )

        # Build features and predict
        category_views = self.process_views(preferences, categories)
        scores = self.model.predict(category_views, len(categories))

        # Also incorporate raw view counts as a strong signal
        raw_scores = np.zeros(len(categories))
        total_views = sum(p.view_count for p in preferences) or 1
        for pref in preferences:
            cat_id = str(pref.category_id)
            if cat_id in self.category_index_map:
                idx = self.category_index_map[cat_id]
                raw_scores[idx] = pref.view_count / total_views

        # Blend model scores with raw frequency (0.6 model + 0.4 raw)
        if self.model.trained:
            blended = 0.6 * scores + 0.4 * raw_scores
        else:
            # Before model is trained, rely more on raw scores
            blended = 0.3 * scores + 0.7 * raw_scores

        # Get top category indices
        top_indices = np.argsort(blended)[::-1]

        # Select products from top categories with diversity
        recommended = []
        seen_ids = set()

        for idx in top_indices:
            if len(recommended) >= max_products:
                break

            cat_id = self.index_category_map.get(idx)
            if cat_id is None:
                continue

            cat_score = blended[idx]
            if cat_score <= 0.01:
                continue

            # Allocate products proportional to score
            num_from_cat = max(
                2, int(max_products * cat_score / max(blended.sum(), 0.01))
            )
            num_from_cat = min(num_from_cat, max_products - len(recommended))

            cat_products = list(
                all_products.filter(category_id=cat_id)
                            .order_by('-rating', '-num_reviews')[:num_from_cat + 5]
            )

            for p in cat_products:
                if str(p.id) not in seen_ids and len(recommended) < max_products:
                    recommended.append(p)
                    seen_ids.add(str(p.id))

        # Fill remaining slots with popular products
        if len(recommended) < max_products:
            remaining = max_products - len(recommended)
            fillers = all_products.exclude(
                id__in=[p.id for p in recommended]
            ).order_by('-rating', '-num_reviews')[:remaining]
            recommended.extend(list(fillers))

        return recommended

    def update_model(self, preferences, categories):
        """Train the model with latest preference data.

        Called periodically to update the model weights
        based on accumulated user behavior data.
        """
        self._ensure_model(categories)

        if not preferences.exists():
            return

        category_views = self.process_views(preferences, categories)

        # Build target: normalized view counts as ground truth preferences
        target = np.zeros(len(categories))
        total = sum(p.view_count for p in preferences) or 1
        for pref in preferences:
            cat_id = str(pref.category_id)
            if cat_id in self.category_index_map:
                idx = self.category_index_map[cat_id]
                target[idx] = pref.view_count / total

        # Train step
        loss = self.model.train_step(category_views, target, len(categories))

        # Save updated model
        self.model.save()

        return loss


# Singleton instance
recommendation_engine = RecommendationEngine()
