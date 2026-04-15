"""
Deep Learning Models for Customer Behavior Analysis.

This module defines four PyTorch neural network architectures:

1. CustomerBehaviorAutoencoder - Compresses customer behavioral features into
   a dense embedding vector. Used for customer segmentation and as input features
   for downstream tasks.

2. ChurnPredictionNetwork - Multi-layer perceptron that predicts the probability
   of a customer churning (not returning to purchase).

3. CLVPredictionNetwork - Regression network that predicts the Customer Lifetime
   Value (total expected revenue from a customer).

4. PurchaseSequenceModel - LSTM-based model that takes a sequence of purchase
   events (category, amount, time delta) and predicts the next category the
   customer is likely to purchase from.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CustomerBehaviorAutoencoder(nn.Module):
    """
    Variational-inspired Autoencoder for customer behavior embedding.

    Takes a feature vector describing the customer's purchasing behavior
    (RFM, category distributions, time patterns, etc.) and compresses
    it into a dense latent vector. This vector serves as the customer embedding
    used for segmentation (clustering) and as auxiliary input for other models.

    Architecture:
        Encoder: input_dim → 128 → 64 → embedding_dim
        Decoder: embedding_dim → 64 → 128 → input_dim
        With BatchNorm and LeakyReLU activations, plus dropout for regularization.
    """

    def __init__(self, input_dim, embedding_dim=32):
        super().__init__()
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),

            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.2),

            nn.Linear(64, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.Tanh(),
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.2),

            nn.Linear(64, 128),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),

            nn.Linear(128, input_dim),
        )

    def encode(self, x):
        """Encode input features into embedding vector."""
        return self.encoder(x)

    def decode(self, z):
        """Decode embedding vector back to feature space."""
        return self.decoder(z)

    def forward(self, x):
        """Forward pass: encode then decode."""
        z = self.encode(x)
        reconstructed = self.decode(z)
        return reconstructed, z


class ChurnPredictionNetwork(nn.Module):
    """
    Deep neural network for customer churn prediction.

    Takes customer behavioral features (optionally concatenated with their
    autoencoder embedding) and outputs a churn probability.

    Architecture:
        input_dim → 128 → 64 → 32 → 16 → 1 (sigmoid)
        With residual connections, BatchNorm, and dropout for generalization.
    """

    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

        self.block1 = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.4),
        )

        self.block2 = nn.Sequential(
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
        )

        self.block3 = nn.Sequential(
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.2),
        )

        self.block4 = nn.Sequential(
            nn.Linear(32, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
        )

        self.output = nn.Linear(16, 1)

    def forward(self, x):
        """Forward pass returns churn probability."""
        h = self.block1(x)
        h = self.block2(h)
        h = self.block3(h)
        h = self.block4(h)
        return torch.sigmoid(self.output(h))


class CLVPredictionNetwork(nn.Module):
    """
    Regression network for Customer Lifetime Value prediction.

    Predicts the total expected revenue from a customer. Uses a deeper
    architecture with skip connections for better gradient flow.

    Architecture:
        input_dim → 256 → 128 → 64 → 32 → 1
        With skip connections between compatible layers.
    """

    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

        self.fc1 = nn.Linear(input_dim, 256)
        self.bn1 = nn.BatchNorm1d(256)

        self.fc2 = nn.Linear(256, 128)
        self.bn2 = nn.BatchNorm1d(128)

        self.fc3 = nn.Linear(128, 64)
        self.bn3 = nn.BatchNorm1d(64)

        self.fc4 = nn.Linear(64, 32)
        self.bn4 = nn.BatchNorm1d(32)

        self.output = nn.Linear(32, 1)

        # Skip connection projections
        self.skip_1_to_3 = nn.Linear(256, 64)

        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        """Forward pass returns predicted CLV (non-negative via ReLU)."""
        h1 = F.relu(self.bn1(self.fc1(x)))
        h1 = self.dropout(h1)

        h2 = F.relu(self.bn2(self.fc2(h1)))
        h2 = self.dropout(h2)

        # Skip connection: h1 → h3
        skip = self.skip_1_to_3(h1)
        h3 = F.relu(self.bn3(self.fc3(h2)) + skip)
        h3 = self.dropout(h3)

        h4 = F.relu(self.bn4(self.fc4(h3)))

        # ReLU on output to ensure non-negative CLV
        return F.relu(self.output(h4))


class PurchaseSequenceModel(nn.Module):
    """
    LSTM-based model for sequential purchase prediction.

    Takes a sequence of purchase events represented as
    (category_index, normalized_amount, time_delta_days) and predicts
    which category the customer will purchase from next.

    Architecture:
        Category Embedding(num_categories, 32)
        → Concat with amount and time features
        → LSTM(hidden=128, layers=2, bidirectional)
        → Attention mechanism over hidden states
        → FC → num_categories (softmax)
    """

    def __init__(self, num_categories, category_embed_dim=32,
                 hidden_dim=128, num_layers=2):
        super().__init__()
        self.num_categories = num_categories
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Category embedding
        self.category_embedding = nn.Embedding(num_categories + 1, category_embed_dim,
                                                padding_idx=0)

        # Input: category_embed + amount + time_delta = category_embed_dim + 2
        lstm_input_dim = category_embed_dim + 2

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=lstm_input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.3 if num_layers > 1 else 0,
            bidirectional=True,
        )

        # Attention layer
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_categories),
        )

    def forward(self, category_seq, amount_seq, time_delta_seq):
        """
        Forward pass.

        Args:
            category_seq: (batch, seq_len) - category indices
            amount_seq: (batch, seq_len) - normalized purchase amounts
            time_delta_seq: (batch, seq_len) - days between purchases

        Returns:
            logits: (batch, num_categories) - prediction scores
        """
        # Embed categories
        cat_embed = self.category_embedding(category_seq)  # (B, S, embed_dim)

        # Concat features
        amount_feat = amount_seq.unsqueeze(-1)  # (B, S, 1)
        time_feat = time_delta_seq.unsqueeze(-1)  # (B, S, 1)
        x = torch.cat([cat_embed, amount_feat, time_feat], dim=-1)  # (B, S, embed+2)

        # LSTM
        lstm_out, _ = self.lstm(x)  # (B, S, hidden*2)

        # Attention
        attn_weights = self.attention(lstm_out)  # (B, S, 1)
        attn_weights = F.softmax(attn_weights, dim=1)
        context = torch.sum(lstm_out * attn_weights, dim=1)  # (B, hidden*2)

        # Predict next category
        logits = self.fc(context)  # (B, num_categories)
        return logits
