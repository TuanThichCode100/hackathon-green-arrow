"""
Measures held-out performance for each persisted (disaster, horizon) cell
produced by training.py, and writes a report + diagnostic plots to
docs/eval/<disaster>_<horizon>/ -- a dedicated folder per cell.

Re-scores the exact held-out block recorded in the cell's artifact
("headline_test_block", set by training.train_cell) rather than re-deriving
fold boundaries independently, so evaluation and training always agree on
what "test" means for a given cell.

Per docs/training_plan.md §6, PR-AUC, F2/F3 (at the frozen threshold) and
Brier score are the headline numbers under this class imbalance. ROC-AUC and
accuracy are included for completeness/visualization only -- the plan
explicitly warns ROC-AUC can look strong even when precision at the
operating point is poor, so they are not the numbers to make a ship/no-ship
call on.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

import joblib
from training import (
    DEFAULT_FEATURES_PATH,
    DEFAULT_OUTPUT_DIR,
    DISASTERS,
    HORIZONS,
    _block_mask,
    add_windowed_labels,
    load_features,
)

DEFAULT_EVAL_DIR = Path(__file__).resolve().parents[2] / "docs" / "eval"


def generate_evaluation_report(
    y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5, probabilistic: bool = True
) -> dict:
    """Flat dict of scalar metrics for one held-out block: PR-AUC/F2/F3 first
    (headline, plan §6), then precision/recall/F1, then ROC-AUC/accuracy last
    (diagnostic only -- do not headline these under heavy class imbalance)."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    y_pred = (y_score >= threshold).astype(int)
    has_both_classes = len(np.unique(y_true)) > 1

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    def f_beta(beta: float) -> float:
        denom = beta**2 * precision + recall
        return (1 + beta**2) * precision * recall / denom if denom else 0.0

    metrics = {
        "pr_auc": float(average_precision_score(y_true, y_score)) if has_both_classes else float("nan"),
        "f2": f_beta(2.0),
        "f3": f_beta(3.0),
        "precision": precision,
        "recall": recall,
        "f1": f_beta(1.0),
        "threshold": float(threshold),
        "n_pos": float(y_true.sum()),
        "n": float(len(y_true)),
        "roc_auc": float(roc_auc_score(y_true, y_score)) if has_both_classes else float("nan"),
        "accuracy": float(accuracy_score(y_true, y_pred)),
    }
    if probabilistic:
        metrics["brier_score"] = float(brier_score_loss(y_true, y_score))
    return metrics


def plot_roc_curve(y_true: np.ndarray, y_score: np.ndarray, save_path: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score) if len(np.unique(y_true)) > 1 else float("nan")
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, label=f"AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve (diagnostic only -- see PR curve for the headline metric)")
    ax.legend()
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def plot_precision_recall_curve(y_true: np.ndarray, y_score: np.ndarray, save_path: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score) if len(np.unique(y_true)) > 1 else float("nan")
    prevalence = float(np.mean(y_true))
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(recall, precision, label=f"PR-AUC = {ap:.3f}")
    ax.axhline(prevalence, linestyle="--", color="gray", label=f"No-skill ({prevalence:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve (headline metric)")
    ax.legend()
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, save_path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], labels=["No event", "Event"])
    ax.set_yticks([0, 1], labels=["No event", "Event"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (frozen threshold)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def plot_feature_importance(model, feature_names: list[str], save_path: Path) -> None:
    importances = model.feature_importances_
    order = np.argsort(importances)
    fig, ax = plt.subplots(figsize=(6, max(3, 0.4 * len(feature_names))))
    ax.barh(np.array(feature_names)[order], importances[order])
    ax.set_xlabel("Importance (gain-based)")
    ax.set_title("Feature Importance")
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def plot_lift_curve(y_true: np.ndarray, y_score: np.ndarray, save_path: Path, n_bins: int = 10) -> None:
    order = np.argsort(-y_score)
    y_sorted = np.asarray(y_true)[order]
    overall_rate = y_sorted.mean() if len(y_sorted) else 0.0
    bin_edges = np.linspace(0, len(y_sorted), n_bins + 1).astype(int)
    lifts = []
    for i in range(n_bins):
        chunk = y_sorted[bin_edges[i] : bin_edges[i + 1]]
        rate = chunk.mean() if len(chunk) else 0.0
        lifts.append(rate / overall_rate if overall_rate else 0.0)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(range(1, n_bins + 1), lifts)
    ax.axhline(1.0, linestyle="--", color="gray", label="No-skill (lift=1)")
    ax.set_xlabel("Decile (1 = highest predicted score)")
    ax.set_ylabel("Lift")
    ax.set_title("Lift Curve")
    ax.legend()
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def plot_probability_distribution(y_true: np.ndarray, y_score: np.ndarray, save_path: Path) -> None:
    y_true = np.asarray(y_true)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.hist(y_score[y_true == 0], bins=30, alpha=0.6, label="No event", density=True)
    ax.hist(y_score[y_true == 1], bins=30, alpha=0.6, label="Event", density=True)
    ax.set_xlabel("Predicted score")
    ax.set_ylabel("Density")
    ax.set_title("Predicted Score Distribution by Class")
    ax.legend()
    fig.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def _load_headline_test_set(artifact: dict, disaster: str, features_path: Path):
    df = load_features(features_path)
    labeled = add_windowed_labels(df, artifact["horizon_hours"], artifact["window_hours"])
    valid_df = labeled.loc[labeled[disaster].notna()].reset_index(drop=True)

    test_block = artifact["headline_test_block"]
    if test_block is None:
        raise ValueError(f"No evaluable held-out block recorded for '{disaster}' -- too little history for a fold.")
    test_mask = _block_mask(valid_df["time"], test_block)
    return valid_df.loc[test_mask].reset_index(drop=True)


def evaluate_cell(
    disaster: str,
    horizon: str,
    models_dir: Path = DEFAULT_OUTPUT_DIR,
    features_path: Path = DEFAULT_FEATURES_PATH,
    eval_dir: Path = DEFAULT_EVAL_DIR,
) -> dict:
    """Evaluate one persisted (disaster, horizon) cell on its recorded
    held-out block: metrics + the plot suite, written to
    docs/eval/<disaster>_<horizon>/ (plan §6)."""
    artifact = joblib.load(models_dir / f"{disaster}_{horizon}.pkl")
    test_df = _load_headline_test_set(artifact, disaster, features_path)
    y_true = test_df[disaster].astype(int).to_numpy()

    is_model = artifact["model"] is not None
    if is_model:
        X = test_df[artifact["features"]]
        y_score = artifact["calibrator"].predict_proba(X)[:, 1]
    else:
        feature, direction = artifact["rule"]["feature"], artifact["rule"]["direction"]
        raw = test_df[feature].to_numpy()
        y_score = raw if direction == "high" else -raw

    threshold = artifact["threshold"] if artifact["threshold"] is not None else float(np.median(y_score))
    y_pred = (y_score >= threshold).astype(int)

    cell_dir = eval_dir / f"{disaster}_{horizon}"
    cell_dir.mkdir(parents=True, exist_ok=True)

    kind = "model" if is_model else "baseline rule"
    print(f"\n{'=' * 60}\nEvaluating {disaster} / {horizon} ({kind})\n{'=' * 60}")

    print("\nEvaluation Metrics:")
    metrics = generate_evaluation_report(y_true, y_score, threshold=threshold, probabilistic=is_model)
    for name, value in metrics.items():
        print(f"   {name}: {value:.4f}")

    print("\nGenerating visualizations...")
    plot_roc_curve(y_true, y_score, cell_dir / "roc_curve.png")
    plot_precision_recall_curve(y_true, y_score, cell_dir / "pr_curve.png")
    plot_confusion_matrix(y_true, y_pred, cell_dir / "confusion_matrix.png")
    if is_model:
        plot_feature_importance(artifact["model"], artifact["features"], cell_dir / "feature_importance.png")
    plot_lift_curve(y_true, y_score, cell_dir / "lift_curve.png")
    plot_probability_distribution(y_true, y_score, cell_dir / "probability_distribution.png")

    report = {
        "disaster": disaster,
        "horizon": horizon,
        "kind": "model" if is_model else "baseline_rule",
        "tier": artifact["tier"],
        "threshold": float(threshold),
        "test_block": [str(b) for b in artifact["headline_test_block"]],
        "metrics": metrics,
    }
    with open(cell_dir / "metrics.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to {cell_dir}")
    return report


def run_evaluation_pipeline(
    models_dir: Path = DEFAULT_OUTPUT_DIR,
    features_path: Path = DEFAULT_FEATURES_PATH,
    eval_dir: Path = DEFAULT_EVAL_DIR,
) -> list[dict]:
    """Evaluate every persisted cell found in `models_dir` (skips cells that
    haven't been trained yet)."""
    reports = []
    for horizon_name in HORIZONS:
        for disaster in DISASTERS:
            artifact_path = models_dir / f"{disaster}_{horizon_name}.pkl"
            if not artifact_path.exists():
                continue
            reports.append(evaluate_cell(disaster, horizon_name, models_dir, features_path, eval_dir))
    return reports


if __name__ == "__main__":
    run_evaluation_pipeline()
