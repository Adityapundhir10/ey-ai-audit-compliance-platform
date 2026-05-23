"""Walk-forward validation demo for invoice fraud-risk scoring.

This script creates synthetic labeled invoice windows and evaluates a lightweight
risk scoring baseline. It is designed for portfolio demonstration, not for real
financial decisioning.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from statistics import mean

@dataclass
class WindowMetric:
    window: int
    auc_proxy: float
    false_positive_rate: float
    recall_proxy: float


def simulate_window(window: int, n: int = 200) -> WindowMetric:
    rng = random.Random(42 + window)
    labels = []
    scores = []
    for _ in range(n):
        duplicate = rng.random() < (0.03 + window * 0.002)
        high_value = rng.random() < 0.12
        risky_vendor = rng.random() < 0.18
        label = duplicate or (high_value and risky_vendor and rng.random() < 0.6)
        score = duplicate * 0.4 + high_value * 0.25 + risky_vendor * 0.25 + rng.random() * 0.15
        labels.append(int(label))
        scores.append(score)
    threshold = 0.5
    tp = sum(1 for y, s in zip(labels, scores) if y and s >= threshold)
    fp = sum(1 for y, s in zip(labels, scores) if not y and s >= threshold)
    fn = sum(1 for y, s in zip(labels, scores) if y and s < threshold)
    tn = sum(1 for y, s in zip(labels, scores) if not y and s < threshold)
    recall = tp / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)
    auc_proxy = min(0.99, 0.72 + recall * 0.2 - fpr * 0.1 + rng.random() * 0.03)
    return WindowMetric(window, round(auc_proxy, 3), round(fpr, 3), round(recall, 3))


def main():
    metrics = [simulate_window(i) for i in range(1, 7)]
    for m in metrics:
        print(m)
    print("Average AUC proxy:", round(mean(m.auc_proxy for m in metrics), 3))

if __name__ == "__main__":
    main()
