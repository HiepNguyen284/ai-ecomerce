"""
Behavior Prediction Models: RNN, LSTM, BiLSTM

Predicts the NEXT user action based on a sequence of previous actions.
Task: 8-class classification (view, click, search, add_to_cart,
      add_to_wishlist, purchase, review, share)

Input:  sequence of N past actions (encoded as integers)
Output: predicted next action (one of 8 classes)
"""

import torch
import torch.nn as nn


# ──────────────────────────────────────────────
# Model 1: Simple RNN
# ──────────────────────────────────────────────
class RNNClassifier(nn.Module):
    """Simple (Elman) RNN for action sequence classification."""

    def __init__(self, num_actions=8, embed_dim=32, hidden_dim=64,
                 num_layers=2, dropout=0.3):
        super().__init__()
        self.model_name = 'RNN'
        self.embedding = nn.Embedding(num_actions, embed_dim)
        self.rnn = nn.RNN(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, num_actions)

    def forward(self, x):
        # x: (batch, seq_len)
        embedded = self.embedding(x)           # (batch, seq_len, embed_dim)
        out, _ = self.rnn(embedded)             # (batch, seq_len, hidden_dim)
        last_hidden = out[:, -1, :]             # (batch, hidden_dim)
        last_hidden = self.dropout(last_hidden)
        logits = self.fc(last_hidden)           # (batch, num_actions)
        return logits


# ──────────────────────────────────────────────
# Model 2: LSTM
# ──────────────────────────────────────────────
class LSTMClassifier(nn.Module):
    """LSTM for action sequence classification."""

    def __init__(self, num_actions=8, embed_dim=32, hidden_dim=64,
                 num_layers=2, dropout=0.3):
        super().__init__()
        self.model_name = 'LSTM'
        self.embedding = nn.Embedding(num_actions, embed_dim)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, num_actions)

    def forward(self, x):
        embedded = self.embedding(x)
        out, (h_n, c_n) = self.lstm(embedded)
        last_hidden = out[:, -1, :]
        last_hidden = self.dropout(last_hidden)
        logits = self.fc(last_hidden)
        return logits


# ──────────────────────────────────────────────
# Model 3: Bidirectional LSTM
# ──────────────────────────────────────────────
class BiLSTMClassifier(nn.Module):
    """Bidirectional LSTM for action sequence classification."""

    def __init__(self, num_actions=8, embed_dim=32, hidden_dim=64,
                 num_layers=2, dropout=0.3):
        super().__init__()
        self.model_name = 'BiLSTM'
        self.embedding = nn.Embedding(num_actions, embed_dim)
        self.bilstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(dropout)
        # BiLSTM outputs hidden_dim * 2 (forward + backward)
        self.fc = nn.Linear(hidden_dim * 2, num_actions)

    def forward(self, x):
        embedded = self.embedding(x)
        out, _ = self.bilstm(embedded)
        last_hidden = out[:, -1, :]             # (batch, hidden_dim * 2)
        last_hidden = self.dropout(last_hidden)
        logits = self.fc(last_hidden)
        return logits
