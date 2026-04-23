"""
Data preprocessing for behavior sequence models.

Converts raw CSV data into PyTorch-ready sequences for
next-action prediction.
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

# Action encoding (consistent with models.py ACTION_CHOICES)
ACTION_TO_IDX = {
    'view': 0,
    'click': 1,
    'search': 2,
    'add_to_cart': 3,
    'add_to_wishlist': 4,
    'purchase': 5,
    'review': 6,
    'share': 7,
}
IDX_TO_ACTION = {v: k for k, v in ACTION_TO_IDX.items()}
NUM_ACTIONS = len(ACTION_TO_IDX)


class BehaviorSequenceDataset(Dataset):
    """PyTorch Dataset for user behavior action sequences."""

    def __init__(self, sequences, targets):
        self.sequences = torch.LongTensor(sequences)
        self.targets = torch.LongTensor(targets)

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


def load_and_preprocess(csv_path, seq_length=10, test_size=0.2,
                        random_state=42):
    """
    Load CSV and create sliding-window sequences for each user.

    For each user's action timeline:
        [a1, a2, a3, ..., a10, a11] →
            input: [a1..a10], target: a11
            input: [a2..a11], target: a12
            ...

    Args:
        csv_path: path to data_user500.csv
        seq_length: number of past actions to use as input
        test_size: fraction for test split
        random_state: random seed

    Returns:
        train_loader, test_loader, class_weights
    """
    print(f"Loading data from {csv_path} ...")
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['user_id', 'timestamp'])

    # Encode actions
    df['action_idx'] = df['action'].map(ACTION_TO_IDX)

    print(f"  Total records: {len(df)}")
    print(f"  Users: {df['user_id'].nunique()}")
    print(f"  Actions: {df['action'].nunique()}")

    # Build sequences per user
    sequences = []
    targets = []

    user_groups = df.groupby('user_id')['action_idx'].apply(list)

    for user_id, actions in user_groups.items():
        if len(actions) <= seq_length:
            continue
        for i in range(len(actions) - seq_length):
            seq = actions[i:i + seq_length]
            target = actions[i + seq_length]
            sequences.append(seq)
            targets.append(target)

    sequences = np.array(sequences)
    targets = np.array(targets)

    print(f"  Generated {len(sequences)} sequences (window={seq_length})")

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        sequences, targets,
        test_size=test_size,
        random_state=random_state,
        stratify=targets,
    )

    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")

    # Compute class weights (handle imbalanced data)
    class_counts = np.bincount(y_train, minlength=NUM_ACTIONS)
    total = class_counts.sum()
    class_weights = total / (NUM_ACTIONS * class_counts.astype(float) + 1e-8)
    class_weights = torch.FloatTensor(class_weights)

    print(f"  Class distribution (train):")
    for idx, count in enumerate(class_counts):
        pct = count / total * 100
        print(f"    {IDX_TO_ACTION[idx]:>18s}: {count:>6d} ({pct:5.1f}%)")

    # DataLoaders
    train_dataset = BehaviorSequenceDataset(X_train, y_train)
    test_dataset = BehaviorSequenceDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=256, shuffle=False)

    return train_loader, test_loader, class_weights, (X_test, y_test)
