"""Evaluate a saved disaster model on an independent labeled dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from pipeline.inference.predict import load_model
from pipeline.preprocessing.open_meteo import LEGACY_FEATURE_ALIASES
from pipeline.shared.model_bundle import DisasterModelBundle
from pipeline.training.train import (
    LABEL_NAMES,
    TARGET_COLUMNS,
    display_label,
    prepare_training_data,
    read_training_data,
)


def evaluate_model(
    model: DisasterModelBundle, labeled_data: pd.DataFrame
) -> dict[str, Any]:
    """Score a model on labeled data that was not used for training."""

    prepared = prepare_training_data(
        labeled_data, forecast_horizon_hours=model.forecast_horizon_hours
    )
    for canonical, legacy in LEGACY_FEATURE_ALIASES.items():
        if legacy in model.feature_columns and canonical in prepared:
            prepared[legacy] = prepared[canonical]
    probabilities = model.predict_proba(prepared)
    target_reports: dict[str, dict[str, Any]] = {}
    for target in TARGET_COLUMNS:
        labels = prepared[target]
        scores = probabilities[target]
        threshold = model.thresholds[target]
        predictions = scores.ge(threshold)
        both_classes = labels.nunique() == 2
        target_reports[target] = {
            "name": LABEL_NAMES[target],
            "rows": len(labels),
            "positive_rows": int(labels.sum()),
            "prevalence": float(labels.mean()),
            "threshold": threshold,
            "average_precision": float(average_precision_score(labels, scores))
            if both_classes
            else None,
            "roc_auc": float(roc_auc_score(labels, scores))
            if both_classes
            else None,
            "brier_score": float(brier_score_loss(labels, scores)),
            "precision": float(
                precision_score(labels, predictions, zero_division=0)
            ),
            "recall": float(recall_score(labels, predictions, zero_division=0)),
            "f1": float(f1_score(labels, predictions, zero_division=0)),
            "probability_calibrated": model.probability_is_calibrated(target),
        }

    average_precisions = [
        metrics["average_precision"]
        for metrics in target_reports.values()
        if metrics["average_precision"] is not None
    ]
    brier_scores = [metrics["brier_score"] for metrics in target_reports.values()]
    invalid_average_precision_targets = [
        target
        for target, metrics in target_reports.items()
        if metrics["average_precision"] is None
    ]
    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model_created_at": model.created_at,
        "forecast_horizon_hours": model.forecast_horizon_hours,
        "summary": {
            "macro_average_precision": float(np.mean(average_precisions))
            if len(average_precisions) == len(TARGET_COLUMNS)
            else None,
            "average_precision_target_coverage": len(average_precisions),
            "invalid_average_precision_targets": invalid_average_precision_targets,
            "mean_brier_score": float(np.mean(brier_scores)),
        },
        "targets": target_reports,
    }


def _print_summary(report: dict[str, Any]) -> None:
    rows = []
    for target, metrics in report["targets"].items():
        rows.append(
            {
                "target": target,
                "name": display_label(target),
                "prevalence": metrics["prevalence"],
                "PR-AUC": metrics["average_precision"],
                "ROC-AUC": metrics["roc_auc"],
                "Brier": metrics["brier_score"],
                "Precision": metrics["precision"],
                "Recall": metrics["recall"],
                "F1": metrics["f1"],
            }
        )
    print(pd.DataFrame(rows).to_string(index=False))
    print(
        "Macro PR-AUC:",
        report["summary"]["macro_average_precision"],
        "| Mean Brier:",
        report["summary"]["mean_brier_score"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/evaluation.json")
    )
    args = parser.parse_args()

    report = evaluate_model(load_model(args.model), read_training_data(args.data))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _print_summary(report)
    print(f"Evaluation report: {args.output}")


if __name__ == "__main__":
    main()
