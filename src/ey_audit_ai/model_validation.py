from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass
class ValidationFold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


class WalkForwardValidator:
    """Utility for time-aware fraud model validation."""

    def split(self, n_samples: int, train_size: int, test_size: int, step: int | None = None) -> list[ValidationFold]:
        if train_size <= 0 or test_size <= 0:
            raise ValueError("train_size and test_size must be positive")
        step = step or test_size
        folds: list[ValidationFold] = []
        start = 0
        while start + train_size + test_size <= n_samples:
            folds.append(
                ValidationFold(
                    train_start=start,
                    train_end=start + train_size,
                    test_start=start + train_size,
                    test_end=start + train_size + test_size,
                )
            )
            start += step
        return folds


def roc_auc_score_safe(labels: Iterable[int], scores: Iterable[float]) -> float:
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    pos = sum(1 for _, y in pairs if y == 1)
    neg = sum(1 for _, y in pairs if y == 0)
    if pos == 0 or neg == 0:
        return 0.5
    rank_sum = 0.0
    for rank, (_, label) in enumerate(pairs, start=1):
        if label == 1:
            rank_sum += rank
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


def population_stability_index(expected: list[float], actual: list[float], buckets: int = 10) -> float:
    if not expected or not actual:
        return 0.0
    lo, hi = min(expected + actual), max(expected + actual)
    if lo == hi:
        return 0.0
    width = (hi - lo) / buckets
    psi = 0.0
    for i in range(buckets):
        left = lo + i * width
        right = hi if i == buckets - 1 else left + width
        e = sum(1 for x in expected if left <= x <= right) / len(expected)
        a = sum(1 for x in actual if left <= x <= right) / len(actual)
        e = max(e, 1e-6)
        a = max(a, 1e-6)
        psi += (a - e) * math.log(a / e)
    return round(psi, 6)
