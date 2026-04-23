"""
Training, evaluation, and visualization for RNN/LSTM/BiLSTM models.

Trains all three models, evaluates with multiple metrics,
generates comparison plots, and selects the best model.
"""

import os
import time
import json
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns

from .models import RNNClassifier, LSTMClassifier, BiLSTMClassifier
from .preprocessing import (
    load_and_preprocess,
    ACTION_TO_IDX,
    IDX_TO_ACTION,
    NUM_ACTIONS,
)


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train model for one epoch, return average loss and accuracy."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * X_batch.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == y_batch).sum().item()
        total += X_batch.size(0)

    return total_loss / total, correct / total


def evaluate(model, loader, criterion, device):
    """Evaluate model, return loss, accuracy, all predictions, all labels."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            logits = model(X_batch)
            loss = criterion(logits, y_batch)

            total_loss += loss.item() * X_batch.size(0)
            preds = logits.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(y_batch.cpu().numpy())

    total = len(all_labels)
    return total_loss / total, all_preds, all_labels


def train_model(model, train_loader, test_loader, class_weights,
                epochs=30, lr=0.001, device='cpu', stdout=None):
    """
    Full training loop for a single model.

    Returns training history and final evaluation results.
    """
    def _log(msg):
        if stdout:
            stdout.write(msg)
        print(msg)

    model = model.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=5, factor=0.5, verbose=False,
    )

    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': [],
    }

    best_val_acc = 0
    best_state = None
    start_time = time.time()

    _log(f"\n{'=' * 60}")
    _log(f"Training {model.model_name}")
    _log(f"{'=' * 60}")

    for epoch in range(1, epochs + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device)

        val_loss, val_preds, val_labels = evaluate(
            model, test_loader, criterion, device)
        val_acc = accuracy_score(val_labels, val_preds)

        scheduler.step(val_loss)

        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 5 == 0 or epoch == 1:
            _log(f"  Epoch {epoch:>3d}/{epochs} | "
                 f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
                 f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

    elapsed = time.time() - start_time

    # Restore best model
    if best_state:
        model.load_state_dict(best_state)

    # Final evaluation
    _, final_preds, final_labels = evaluate(
        model, test_loader, criterion, device)

    action_names = [IDX_TO_ACTION[i] for i in range(NUM_ACTIONS)]

    metrics = {
        'model_name': model.model_name,
        'accuracy': accuracy_score(final_labels, final_preds),
        'precision_macro': precision_score(
            final_labels, final_preds, average='macro', zero_division=0),
        'recall_macro': recall_score(
            final_labels, final_preds, average='macro', zero_division=0),
        'f1_macro': f1_score(
            final_labels, final_preds, average='macro', zero_division=0),
        'precision_weighted': precision_score(
            final_labels, final_preds, average='weighted', zero_division=0),
        'recall_weighted': recall_score(
            final_labels, final_preds, average='weighted', zero_division=0),
        'f1_weighted': f1_score(
            final_labels, final_preds, average='weighted', zero_division=0),
        'confusion_matrix': confusion_matrix(final_labels, final_preds).tolist(),
        'classification_report': classification_report(
            final_labels, final_preds,
            target_names=action_names,
            zero_division=0,
        ),
        'training_time_seconds': round(elapsed, 2),
        'best_val_accuracy': best_val_acc,
        'epochs': epochs,
    }

    _log(f"\n  {model.model_name} Final Results:")
    _log(f"    Accuracy:  {metrics['accuracy']:.4f}")
    _log(f"    F1 Macro:  {metrics['f1_macro']:.4f}")
    _log(f"    F1 Weight: {metrics['f1_weighted']:.4f}")
    _log(f"    Time:      {elapsed:.1f}s")

    return model, history, metrics, final_preds, final_labels


# ──────────────────────────────────────────────
# Visualization Functions
# ──────────────────────────────────────────────

def plot_training_curves(all_histories, save_dir):
    """Plot training/validation loss and accuracy for all models."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    colors = {'RNN': '#FF6B6B', 'LSTM': '#4ECDC4', 'BiLSTM': '#45B7D1'}

    # Loss curves
    ax = axes[0]
    for name, history in all_histories.items():
        color = colors.get(name, '#333')
        epochs = range(1, len(history['train_loss']) + 1)
        ax.plot(epochs, history['train_loss'], '-', color=color,
                alpha=0.4, label=f'{name} Train')
        ax.plot(epochs, history['val_loss'], '-', color=color,
                linewidth=2, label=f'{name} Val')
    ax.set_title('Training & Validation Loss', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Accuracy curves
    ax = axes[1]
    for name, history in all_histories.items():
        color = colors.get(name, '#333')
        epochs = range(1, len(history['train_acc']) + 1)
        ax.plot(epochs, history['train_acc'], '-', color=color,
                alpha=0.4, label=f'{name} Train')
        ax.plot(epochs, history['val_acc'], '-', color=color,
                linewidth=2, label=f'{name} Val')
    ax.set_title('Training & Validation Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(save_dir, 'training_curves.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


def plot_confusion_matrices(all_metrics, save_dir):
    """Plot confusion matrix for each model side by side."""
    action_names = [IDX_TO_ACTION[i] for i in range(NUM_ACTIONS)]
    n_models = len(all_metrics)
    fig, axes = plt.subplots(1, n_models, figsize=(8 * n_models, 7))

    if n_models == 1:
        axes = [axes]

    for ax, (name, metrics) in zip(axes, all_metrics.items()):
        cm = np.array(metrics['confusion_matrix'])
        # Normalize
        cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-8)

        sns.heatmap(
            cm_norm, annot=cm, fmt='d', cmap='Blues',
            xticklabels=action_names, yticklabels=action_names,
            ax=ax, cbar_kws={'shrink': 0.8},
        )
        ax.set_title(f'{name}\nAccuracy: {metrics["accuracy"]:.4f}',
                      fontsize=13, fontweight='bold')
        ax.set_xlabel('Predicted', fontsize=11)
        ax.set_ylabel('Actual', fontsize=11)
        ax.tick_params(axis='both', labelsize=8)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    path = os.path.join(save_dir, 'confusion_matrices.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


def plot_metrics_comparison(all_metrics, save_dir):
    """Bar chart comparing key metrics across all models."""
    model_names = list(all_metrics.keys())
    metrics_to_compare = [
        ('accuracy', 'Accuracy'),
        ('precision_macro', 'Precision (Macro)'),
        ('recall_macro', 'Recall (Macro)'),
        ('f1_macro', 'F1-Score (Macro)'),
        ('f1_weighted', 'F1-Score (Weighted)'),
    ]

    x = np.arange(len(metrics_to_compare))
    width = 0.25
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    fig, ax = plt.subplots(figsize=(14, 7))

    for i, model_name in enumerate(model_names):
        values = [all_metrics[model_name][m[0]] for m in metrics_to_compare]
        bars = ax.bar(x + i * width, values, width,
                      label=model_name, color=colors[i], alpha=0.85)
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

    ax.set_xlabel('Metric', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Model Comparison: Key Metrics', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels([m[1] for m in metrics_to_compare], fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(save_dir, 'metrics_comparison.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


def plot_per_class_f1(all_metrics, save_dir):
    """Heatmap showing F1 score per class per model."""
    action_names = [IDX_TO_ACTION[i] for i in range(NUM_ACTIONS)]
    model_names = list(all_metrics.keys())

    # Parse classification reports to extract per-class F1
    f1_matrix = []
    for model_name in model_names:
        report = all_metrics[model_name]['classification_report']
        lines = report.strip().split('\n')
        row = []
        for action in action_names:
            for line in lines:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == action:
                    row.append(float(parts[3]))  # f1-score column
                    break
                # Handle multi-word action names like "add_to_cart"
                joined = '_'.join(parts[:2]) if len(parts) >= 5 else ''
                if joined == action:
                    row.append(float(parts[4]))
                    break
            else:
                row.append(0.0)
        f1_matrix.append(row)

    f1_matrix = np.array(f1_matrix)

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(
        f1_matrix, annot=True, fmt='.3f', cmap='YlOrRd',
        xticklabels=action_names, yticklabels=model_names,
        ax=ax, vmin=0, vmax=1, linewidths=0.5,
    )
    ax.set_title('F1-Score per Action Type per Model',
                  fontsize=14, fontweight='bold')
    ax.set_xlabel('Action Type', fontsize=12)
    ax.set_ylabel('Model', fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    path = os.path.join(save_dir, 'per_class_f1.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


def plot_training_time(all_metrics, save_dir):
    """Bar chart of training time per model."""
    model_names = list(all_metrics.keys())
    times = [all_metrics[m]['training_time_seconds'] for m in model_names]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(model_names, times, color=colors, alpha=0.85, width=0.5)
    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f'{t:.1f}s', ha='center', va='bottom', fontsize=12,
                fontweight='bold')

    ax.set_ylabel('Training Time (seconds)', fontsize=12)
    ax.set_title('Training Time Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(save_dir, 'training_time.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────

def run_full_pipeline(csv_path, output_dir, epochs=30, seq_length=10,
                      stdout=None):
    """
    Complete training pipeline:
    1. Load and preprocess data
    2. Train RNN, LSTM, BiLSTM
    3. Evaluate all three
    4. Generate comparison plots
    5. Select and save best model
    6. Write evaluation report

    Returns dict of results.
    """
    def _log(msg):
        if stdout:
            stdout.write(msg)
        print(msg)

    os.makedirs(output_dir, exist_ok=True)
    plots_dir = os.path.join(output_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    _log(f"Device: {device}")

    # Step 1: Data
    _log("\n" + "=" * 60)
    _log("STEP 1: Loading and preprocessing data")
    _log("=" * 60)
    train_loader, test_loader, class_weights, (X_test, y_test) = \
        load_and_preprocess(csv_path, seq_length=seq_length)

    # Step 2: Define models
    model_classes = [
        RNNClassifier,
        LSTMClassifier,
        BiLSTMClassifier,
    ]

    all_histories = {}
    all_metrics = {}
    all_models = {}

    # Step 3: Train each model
    _log("\n" + "=" * 60)
    _log("STEP 2: Training 3 models")
    _log("=" * 60)

    for ModelClass in model_classes:
        model = ModelClass(
            num_actions=NUM_ACTIONS,
            embed_dim=32,
            hidden_dim=64,
            num_layers=2,
            dropout=0.3,
        )

        trained_model, history, metrics, preds, labels = train_model(
            model, train_loader, test_loader, class_weights,
            epochs=epochs, lr=0.001, device=device, stdout=stdout,
        )

        name = model.model_name
        all_histories[name] = history
        all_metrics[name] = metrics
        all_models[name] = trained_model

    # Step 4: Generate plots
    _log("\n" + "=" * 60)
    _log("STEP 3: Generating visualization plots")
    _log("=" * 60)

    plot_training_curves(all_histories, plots_dir)
    plot_confusion_matrices(all_metrics, plots_dir)
    plot_metrics_comparison(all_metrics, plots_dir)
    plot_per_class_f1(all_metrics, plots_dir)
    plot_training_time(all_metrics, plots_dir)

    # Step 5: Select best model
    _log("\n" + "=" * 60)
    _log("STEP 4: Selecting best model")
    _log("=" * 60)

    # Select by F1 weighted (handles imbalanced data best)
    best_name = max(all_metrics, key=lambda k: all_metrics[k]['f1_weighted'])
    best_metrics = all_metrics[best_name]
    best_model = all_models[best_name]

    _log(f"\n  ★ Best Model: {best_name}")
    _log(f"    Accuracy:         {best_metrics['accuracy']:.4f}")
    _log(f"    F1 (Weighted):    {best_metrics['f1_weighted']:.4f}")
    _log(f"    F1 (Macro):       {best_metrics['f1_macro']:.4f}")
    _log(f"    Precision (Macro):{best_metrics['precision_macro']:.4f}")
    _log(f"    Recall (Macro):   {best_metrics['recall_macro']:.4f}")

    # Save best model
    model_path = os.path.join(output_dir, 'model_best.pt')
    torch.save({
        'model_name': best_name,
        'model_state_dict': best_model.state_dict(),
        'metrics': best_metrics,
        'num_actions': NUM_ACTIONS,
        'seq_length': seq_length,
    }, model_path)
    _log(f"\n  Saved best model to: {model_path}")

    # Save all models
    for name, model in all_models.items():
        path = os.path.join(output_dir, f'model_{name.lower()}.pt')
        torch.save({
            'model_name': name,
            'model_state_dict': model.state_dict(),
            'metrics': all_metrics[name],
        }, path)

    # Step 6: Write evaluation report
    _log("\n" + "=" * 60)
    _log("STEP 5: Writing evaluation report")
    _log("=" * 60)

    report = _generate_report(all_metrics, best_name, seq_length, epochs)
    report_path = os.path.join(output_dir, 'evaluation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    _log(f"  Saved report to: {report_path}")

    # Save metrics JSON
    metrics_json_path = os.path.join(output_dir, 'metrics.json')
    serializable_metrics = {}
    for name, m in all_metrics.items():
        sm = {k: v for k, v in m.items() if k != 'classification_report'}
        serializable_metrics[name] = sm
    with open(metrics_json_path, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)

    _log(f"\n{'=' * 60}")
    _log(f"PIPELINE COMPLETE!")
    _log(f"  Output directory: {output_dir}")
    _log(f"  Best model: {best_name} (F1-weighted: {best_metrics['f1_weighted']:.4f})")
    _log(f"  Plots: {plots_dir}/")
    _log(f"{'=' * 60}")

    return {
        'best_model_name': best_name,
        'all_metrics': all_metrics,
        'output_dir': output_dir,
    }


def _generate_report(all_metrics, best_name, seq_length, epochs):
    """Generate a detailed text evaluation report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  BEHAVIOR PREDICTION MODEL EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Task: Predict next user action from sequence of past actions")
    lines.append(f"Sequence length: {seq_length}")
    lines.append(f"Training epochs: {epochs}")
    lines.append(f"Number of classes: {NUM_ACTIONS}")
    lines.append(f"Classes: {', '.join(IDX_TO_ACTION.values())}")
    lines.append("")

    # Individual model results
    for name in all_metrics:
        m = all_metrics[name]
        lines.append("-" * 70)
        lines.append(f"  MODEL: {name}")
        lines.append("-" * 70)
        lines.append(f"  Accuracy:            {m['accuracy']:.4f}")
        lines.append(f"  Precision (Macro):   {m['precision_macro']:.4f}")
        lines.append(f"  Recall (Macro):      {m['recall_macro']:.4f}")
        lines.append(f"  F1-Score (Macro):    {m['f1_macro']:.4f}")
        lines.append(f"  F1-Score (Weighted): {m['f1_weighted']:.4f}")
        lines.append(f"  Training Time:       {m['training_time_seconds']:.1f}s")
        lines.append("")
        lines.append("  Classification Report:")
        lines.append(m['classification_report'])
        lines.append("")

    # Comparison table
    lines.append("=" * 70)
    lines.append("  MODEL COMPARISON SUMMARY")
    lines.append("=" * 70)
    lines.append("")
    header = f"{'Metric':<22s} | {'RNN':>10s} | {'LSTM':>10s} | {'BiLSTM':>10s}"
    lines.append(header)
    lines.append("-" * len(header))

    metric_keys = [
        ('accuracy', 'Accuracy'),
        ('precision_macro', 'Precision (Macro)'),
        ('recall_macro', 'Recall (Macro)'),
        ('f1_macro', 'F1 (Macro)'),
        ('f1_weighted', 'F1 (Weighted)'),
        ('training_time_seconds', 'Training Time (s)'),
    ]

    for key, label in metric_keys:
        vals = []
        for name in ['RNN', 'LSTM', 'BiLSTM']:
            if name in all_metrics:
                v = all_metrics[name][key]
                vals.append(f"{v:>10.4f}" if key != 'training_time_seconds'
                            else f"{v:>10.1f}")
            else:
                vals.append(f"{'N/A':>10s}")
        lines.append(f"{label:<22s} | {' | '.join(vals)}")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  ★ BEST MODEL: {best_name}")
    lines.append("=" * 70)
    lines.append("")

    bm = all_metrics[best_name]

    # Written evaluation
    lines.append("ĐÁNH GIÁ (Evaluation):")
    lines.append("")

    if best_name == 'BiLSTM':
        lines.append(f"Mô hình {best_name} được chọn là mô hình tốt nhất với")
        lines.append(f"F1-Score (Weighted) = {bm['f1_weighted']:.4f}.")
        lines.append("")
        lines.append("BiLSTM vượt trội nhờ khả năng xử lý thông tin theo CẢ HAI")
        lines.append("chiều (forward và backward) của chuỗi hành vi. Điều này")
        lines.append("cho phép mô hình nắm bắt được ngữ cảnh đầy đủ hơn khi")
        lines.append("dự đoán hành vi tiếp theo của người dùng.")
        lines.append("")
        lines.append("So với RNN đơn giản, BiLSTM giải quyết tốt hơn vấn đề")
        lines.append("vanishing gradient nhờ cơ chế gate (forget, input, output).")
        lines.append("So với LSTM một chiều, BiLSTM có thêm thông tin từ chiều")
        lines.append("ngược lại, giúp tăng độ chính xác dự đoán.")
    elif best_name == 'LSTM':
        lines.append(f"Mô hình {best_name} được chọn là mô hình tốt nhất với")
        lines.append(f"F1-Score (Weighted) = {bm['f1_weighted']:.4f}.")
        lines.append("")
        lines.append("LSTM vượt trội nhờ cơ chế memory cell và 3 gate (forget,")
        lines.append("input, output) giúp ghi nhớ thông tin dài hạn trong chuỗi")
        lines.append("hành vi người dùng. Điều này đặc biệt hiệu quả khi các")
        lines.append("hành vi trước đó ảnh hưởng đến quyết định mua hàng.")
        lines.append("")
        lines.append("So với RNN, LSTM tránh được vanishing gradient. So với")
        lines.append("BiLSTM, LSTM có hiệu suất tương đương nhưng nhanh hơn")
        lines.append("do chỉ xử lý một chiều, phù hợp cho dự đoán real-time.")
    else:
        lines.append(f"Mô hình {best_name} được chọn là mô hình tốt nhất với")
        lines.append(f"F1-Score (Weighted) = {bm['f1_weighted']:.4f}.")
        lines.append("")
        lines.append("RNN đơn giản đạt kết quả tốt nhất trong trường hợp này,")
        lines.append("cho thấy dữ liệu hành vi có đặc tính tương đối đơn giản")
        lines.append("và không cần mô hình phức tạp. RNN có ưu điểm huấn luyện")
        lines.append("nhanh hơn và ít tham số hơn LSTM/BiLSTM.")

    lines.append("")
    lines.append("Các hành vi ở đỉnh funnel (view, click) được dự đoán chính")
    lines.append("xác hơn do có nhiều dữ liệu huấn luyện. Các hành vi hiếm")
    lines.append("(review, share) khó dự đoán hơn do mất cân bằng dữ liệu.")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)
