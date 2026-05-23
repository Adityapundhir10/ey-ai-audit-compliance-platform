from ey_audit_ai.model_validation import WalkForwardValidator, population_stability_index, roc_auc_score_safe


def test_walk_forward_validator_and_auc():
    folds = WalkForwardValidator().split(n_samples=20, train_size=10, test_size=5)
    assert len(folds) == 2
    auc = roc_auc_score_safe([0, 0, 1, 1], [0.1, 0.2, 0.7, 0.9])
    assert auc == 1.0


def test_psi_detects_shift():
    psi = population_stability_index([1, 1, 2, 2, 3, 3], [3, 3, 4, 4, 5, 5], buckets=3)
    assert psi > 0
