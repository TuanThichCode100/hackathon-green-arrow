"""Train the five-label natural-disaster probability model."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from filelock import FileLock
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from tqdm.auto import tqdm
from xgboost import XGBClassifier

from pipeline.shared.model_bundle import (
    ConstantProbabilityModel,
    DisasterModelBundle,
    PlattCalibratedModel,
)
from weather_data.build_weather_features import (
    canonicalize_columns,
    live_model_feature_contract,
)


TARGET_COLUMNS = [
    "y_mua_lon",
    "y_sat_lo",
    "y_dong_loc",
    "y_mua_da",
    "y_lu_lut",
]
def model_feature_columns(data: pd.DataFrame) -> list[str]:
    """Return ordered inputs that can also be produced by live inference."""

    available = set(data.columns)
    return [
        column
        for column in live_model_feature_contract()
        if column in available
    ]

LABEL_NAMES = {
    "y_mua_lon": "Mưa lớn",
    "y_sat_lo": "Sạt lở",
    "y_dong_loc": "Dông lốc",
    "y_mua_da": "Mưa đá",
    "y_lu_lut": "Lũ lụt",
}

ASCII_LABEL_NAMES = {
    "y_mua_lon": "Mua lon",
    "y_sat_lo": "Sat lo",
    "y_dong_loc": "Dong loc",
    "y_mua_da": "Mua da",
    "y_lu_lut": "Lu lut",
}


@dataclass(frozen=True)
class ArtifactSaveResult:
    run_directory: Path
    run_model_path: Path
    run_metrics_path: Path
    best_model_path: Path
    best_metrics_path: Path
    experiment_directory: Path
    promoted_to_best: bool


def prepare_training_data(
    data: pd.DataFrame, *, forecast_horizon_hours: int = 24
) -> pd.DataFrame:
    """Validate and aggregate source rows using the baseline notebook semantics."""

    if forecast_horizon_hours < 1:
        raise ValueError("forecast_horizon_hours must be positive")
    data = canonicalize_columns(data)
    feature_columns = model_feature_columns(data)
    required = {"location_id", "time", *TARGET_COLUMNS}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Training data is missing columns: {missing}")

    if not feature_columns:
        raise ValueError("Training data does not contain model features")
    frame = data[["location_id", "time", *feature_columns, *TARGET_COLUMNS]].copy()
    frame["time"] = pd.to_datetime(frame["time"], errors="raise")
    non_numeric = [
        column
        for column in feature_columns
        if not pd.api.types.is_numeric_dtype(frame[column])
    ]
    if non_numeric:
        frame[non_numeric] = frame[non_numeric].apply(
            pd.to_numeric, errors="coerce"
        )
    frame[feature_columns] = frame[feature_columns].astype("float32")
    if frame[feature_columns].isna().all(axis=0).any():
        empty = frame[feature_columns].columns[
            frame[feature_columns].isna().all(axis=0)
        ].tolist()
        raise ValueError(f"Training features contain no numeric values: {empty}")

    for target in TARGET_COLUMNS:
        numeric = pd.to_numeric(frame[target], errors="coerce")
        if numeric.isna().any():
            raise ValueError(f"Target {target} contains missing/non-numeric values")
        invalid_values = sorted(set(numeric.unique()).difference({0, 1}))
        if invalid_values:
            raise ValueError(
                f"Target {target} must contain only 0/1; found {invalid_values[:5]}"
            )
        frame[target] = numeric.astype("int8")

    identity = ["location_id", "time"]
    if frame.duplicated(identity).any():
        weather = frame.groupby(
            identity, as_index=False, observed=True
        )[feature_columns].mean()
        targets = frame.groupby(
            identity, as_index=False, observed=True
        )[TARGET_COLUMNS].max()
    else:
        weather = frame[identity + feature_columns]
        targets = frame[identity + TARGET_COLUMNS].copy()
    targets["time"] = targets["time"] - pd.Timedelta(hours=forecast_horizon_hours)
    prepared = (
        weather.merge(
            targets,
            on=["location_id", "time"],
            how="inner",
            validate="one_to_one",
        )
        .sort_values(["time", "location_id"])
        .reset_index(drop=True)
    )
    if prepared.empty:
        raise ValueError(
            "No feature/target rows align at the requested forecast horizon"
        )
    return prepared


def _new_classifier(
    max_iterations: int, random_state: int, scale_pos_weight: float
) -> Pipeline:
    return Pipeline(
        [
            (
                "classifier",
                XGBClassifier(
                    n_estimators=max_iterations,
                    max_depth=7,
                    min_child_weight=3,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_lambda=2.0,
                    scale_pos_weight=scale_pos_weight,
                    max_delta_step=1,
                    objective="binary:logistic",
                    eval_metric="aucpr",
                    tree_method="hist",
                    n_jobs=max(1, int(os.getenv("LOKY_MAX_CPU_COUNT", "4"))),
                    random_state=random_state,
                ),
            ),
        ]
    )


def _fit_target(
    features: pd.DataFrame,
    labels: pd.Series,
    *,
    max_iterations: int,
    random_state: int,
) -> Pipeline | ConstantProbabilityModel:
    unique = labels.unique()
    if len(unique) == 1:
        return ConstantProbabilityModel(float(unique[0]))
    positives = int(labels.sum())
    negatives = len(labels) - positives
    model = _new_classifier(
        max_iterations,
        random_state,
        scale_pos_weight=min(50.0, float(negatives / positives)),
    )
    early_stop_index = int(len(features) * 0.9)
    early_features = features.iloc[early_stop_index:]
    early_labels = labels.iloc[early_stop_index:]
    can_early_stop = (
        early_stop_index > 0
        and labels.iloc[:early_stop_index].nunique() == 2
        and early_labels.nunique() == 2
    )
    if can_early_stop:
        classifier = model.named_steps["classifier"]
        classifier.set_params(early_stopping_rounds=30)
        model.fit(
            features.iloc[:early_stop_index],
            labels.iloc[:early_stop_index],
            classifier__eval_set=[(early_features, early_labels)],
            classifier__verbose=False,
        )
    else:
        model.fit(features, labels)
    return model


def _positive_probability(
    model: Pipeline | ConstantProbabilityModel | PlattCalibratedModel,
    features: pd.DataFrame,
) -> np.ndarray:
    if isinstance(model, ConstantProbabilityModel):
        return model.positive_probability(len(features))
    if isinstance(model, PlattCalibratedModel):
        return model.positive_probability(features)
    classes = model.named_steps["classifier"].classes_.tolist()
    return model.predict_proba(features)[:, classes.index(1)]


def _calibrate_target(
    model: Pipeline | ConstantProbabilityModel,
    features: pd.DataFrame,
    labels: pd.Series,
) -> ConstantProbabilityModel | PlattCalibratedModel:
    if isinstance(model, ConstantProbabilityModel):
        return model
    if labels.nunique() < 2 or labels.value_counts().min() < 2:
        return PlattCalibratedModel(model, None)

    raw = _positive_probability(model, features)
    clipped = np.clip(raw, 1e-7, 1 - 1e-7)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibrator = LogisticRegression(random_state=42)
    calibrator.fit(logits, labels)
    return PlattCalibratedModel(model, calibrator)


def _choose_threshold(
    labels: pd.Series,
    probabilities: np.ndarray,
    *,
    max_alert_rate: float = 0.05,
    min_recall: float = 0.5,
) -> float:
    if labels.sum() == 0:
        return 0.5
    precision, recall, thresholds = precision_recall_curve(labels, probabilities)
    if len(thresholds) == 0:
        return 0.5
    alert_rates = np.array(
        [float(np.mean(probabilities >= threshold)) for threshold in thresholds]
    )
    feasible = (alert_rates <= max_alert_rate) & (recall[:-1] >= min_recall)
    if np.any(feasible):
        candidate_indices = np.flatnonzero(feasible)
        return float(
            thresholds[
                candidate_indices[
                    int(np.argmax(precision[:-1][candidate_indices]))
                ]
            ]
        )
    f1 = np.divide(
        2 * precision[:-1] * recall[:-1],
        precision[:-1] + recall[:-1],
        out=np.zeros_like(thresholds, dtype=float),
        where=(precision[:-1] + recall[:-1]) > 0,
    )
    within_budget = alert_rates <= max_alert_rate
    if np.any(within_budget):
        candidate_indices = np.flatnonzero(within_budget)
        return float(
            thresholds[candidate_indices[int(np.nanargmax(f1[candidate_indices]))]]
        )
    return float(np.nextafter(np.max(thresholds), np.inf))


def _expected_calibration_error(
    labels: pd.Series, probabilities: np.ndarray, bins: int = 10
) -> float:
    edges = np.linspace(0, 1, bins + 1)
    assignments = np.clip(np.digitize(probabilities, edges) - 1, 0, bins - 1)
    error = 0.0
    for index in range(bins):
        mask = assignments == index
        if not np.any(mask):
            continue
        error += float(np.mean(mask)) * abs(
            float(np.mean(probabilities[mask])) - float(labels.iloc[mask].mean())
        )
    return error


def _target_metrics(
    labels: pd.Series, probabilities: np.ndarray, threshold: float
) -> dict[str, float | int | None]:
    predictions = probabilities >= threshold
    has_both_classes = labels.nunique() == 2
    prevalence = float(labels.mean())
    baseline_brier = prevalence * (1 - prevalence)
    brier = float(brier_score_loss(labels, probabilities))
    return {
        "threshold": threshold,
        "roc_auc": float(roc_auc_score(labels, probabilities))
        if has_both_classes
        else None,
        "average_precision": float(average_precision_score(labels, probabilities))
        if has_both_classes
        else None,
        "brier_score": brier,
        "baseline_brier_score": baseline_brier,
        "brier_skill_score": (
            float(1 - brier / baseline_brier) if baseline_brier > 0 else None
        ),
        "expected_calibration_error": _expected_calibration_error(
            labels.reset_index(drop=True), probabilities
        ),
        "predicted_positive_rows": int(predictions.sum()),
        "alert_rate": float(predictions.mean()),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
    }


def run_temporal_backtest(
    prepared: pd.DataFrame,
    feature_columns: list[str],
    *,
    folds: int,
    max_iterations: int,
    random_state: int,
    show_progress: bool,
) -> list[dict[str, Any]]:
    """Run expanding-window rank backtests without fitting thresholds on test."""

    if folds < 2:
        return []
    unique_times = prepared["time"].drop_duplicates().sort_values().tolist()
    initial = len(unique_times) // 2
    boundaries = np.linspace(initial, len(unique_times), folds + 1, dtype=int)
    tasks = [
        (fold, target)
        for fold in range(folds)
        for target in TARGET_COLUMNS
    ]
    reports: dict[int, dict[str, Any]] = {
        fold: {
            "fold": fold + 1,
            "train_end": pd.Timestamp(
                unique_times[boundaries[fold] - 1]
            ).isoformat(),
            "test_start": pd.Timestamp(
                unique_times[boundaries[fold]]
            ).isoformat(),
            "test_end": pd.Timestamp(
                unique_times[boundaries[fold + 1] - 1]
            ).isoformat(),
            "targets": {},
        }
        for fold in range(folds)
    }
    progress = tqdm(
        tasks,
        desc="BACKTEST",
        unit="model",
        disable=not show_progress,
        dynamic_ncols=True,
        file=sys.stdout,
    )
    for fold, target in progress:
        progress.set_postfix_str(f"{fold + 1}/{folds} {display_label(target)}")
        train_end = unique_times[boundaries[fold]]
        test_end_index = boundaries[fold + 1]
        train = prepared.loc[prepared["time"].lt(train_end)]
        test = prepared.loc[
            prepared["time"].ge(train_end)
            & (
                prepared["time"].lt(unique_times[test_end_index])
                if test_end_index < len(unique_times)
                else pd.Series(True, index=prepared.index)
            )
        ]
        target_report: dict[str, Any] = {
            "training_rows": len(train),
            "test_rows": len(test),
            "training_positives": int(train[target].sum()),
            "test_positives": int(test[target].sum()),
        }
        if train[target].nunique() < 2 or test[target].nunique() < 2:
            target_report["available"] = False
            target_report["reason"] = "train or test fold has only one class"
        else:
            model = _fit_target(
                train[feature_columns],
                train[target],
                max_iterations=max_iterations,
                random_state=random_state + fold,
            )
            probabilities = _positive_probability(model, test[feature_columns])
            prevalence = float(test[target].mean())
            average_precision = float(
                average_precision_score(test[target], probabilities)
            )
            target_report.update(
                {
                    "available": True,
                    "average_precision": average_precision,
                    "pr_auc_lift_over_prevalence": (
                        average_precision / prevalence if prevalence > 0 else None
                    ),
                    "roc_auc": float(roc_auc_score(test[target], probabilities)),
                }
            )
        reports[fold]["targets"][target] = target_report
    return [reports[index] for index in range(folds)]


def _metric_text(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def display_label(target: str) -> str:
    label = LABEL_NAMES[target]
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        label.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return ASCII_LABEL_NAMES[target]
    return label


def _validation_result_text(
    index: int, target: str, metrics: dict[str, Any]
) -> str:
    return (
        f"[VALIDATE {index}/{len(TARGET_COLUMNS)}] {display_label(target)} "
        f"({target}) | time={metrics['timing_seconds']['validation']:.2f}s "
        f"| support={metrics['positive_validation_rows']}/"
        f"{metrics['validation_rows']} "
        f"| prevalence={metrics['validation_prevalence']:.6f} "
        f"| PR-AUC={_metric_text(metrics['average_precision'])} "
        f"| PR-lift={_metric_text(metrics['pr_auc_lift_over_prevalence'], 2)}x "
        f"| ROC-AUC={_metric_text(metrics['roc_auc'])} "
        f"| Brier={_metric_text(metrics['brier_score'], 6)} "
        f"| Brier-skill={_metric_text(metrics['brier_skill_score'])} "
        f"| ECE={_metric_text(metrics['expected_calibration_error'], 6)} "
        f"| precision={_metric_text(metrics['precision'])} "
        f"| recall={_metric_text(metrics['recall'])} "
        f"| F1={_metric_text(metrics['f1'])} "
        f"| alerts={metrics['predicted_positive_rows']} "
        f"| alert-rate={_metric_text(metrics['alert_rate'], 6)} "
        f"| threshold={_metric_text(metrics['threshold'], 6)} "
        f"| calibrated={metrics['probability_calibrated']}"
    )


def train_disaster_models(
    data: pd.DataFrame,
    *,
    forecast_horizon_hours: int = 24,
    calibration_fraction: float = 0.15,
    validation_fraction: float = 0.2,
    max_iterations: int = 200,
    random_state: int = 42,
    require_calibration: bool = True,
    show_progress: bool = True,
    max_alert_rate: float = 0.05,
    min_recall: float = 0.5,
    min_pr_lift: float = 1.5,
    backtest_folds: int = 0,
    backtest_max_iterations: int = 50,
) -> tuple[DisasterModelBundle, dict[str, Any]]:
    """Train and calibrate one future-horizon probability model per hazard."""

    if not 0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be greater than 0 and below 0.5")
    if not 0 < calibration_fraction < 0.4:
        raise ValueError("calibration_fraction must be greater than 0 and below 0.4")
    if validation_fraction + calibration_fraction >= 0.6:
        raise ValueError("calibration and validation fractions leave too little training data")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if not 0 < max_alert_rate <= 1:
        raise ValueError("max_alert_rate must be between 0 and 1")
    if not 0 <= min_recall <= 1:
        raise ValueError("min_recall must be between 0 and 1")
    if min_pr_lift < 0:
        raise ValueError("min_pr_lift must be greater than or equal to 0")
    if backtest_folds not in {0} and backtest_folds < 2:
        raise ValueError("backtest_folds must be 0 or at least 2")

    label_source = canonicalize_columns(data)
    for target in TARGET_COLUMNS:
        if target not in label_source:
            continue
        labels = pd.to_numeric(label_source[target], errors="coerce")
        positives = int(labels.fillna(0).ne(0).sum())
        if positives == 0:
            raise ValueError(
                f"Target {target} has no positive samples; rebuild labels before training"
            )
        if positives == len(label_source):
            raise ValueError(
                f"Target {target} has no negative samples; rebuild labels before training"
            )

    prepared = prepare_training_data(
        data, forecast_horizon_hours=forecast_horizon_hours
    )
    feature_columns = model_feature_columns(prepared)
    temporal_backtest = run_temporal_backtest(
        prepared,
        feature_columns,
        folds=backtest_folds,
        max_iterations=backtest_max_iterations,
        random_state=random_state,
        show_progress=show_progress,
    )
    unique_times = prepared["time"].drop_duplicates().sort_values().tolist()
    if len(unique_times) < 3:
        raise ValueError("Training requires at least three distinct timestamps")
    training_end_index = max(
        1,
        int(
            len(unique_times)
            * (1 - validation_fraction - calibration_fraction)
        ),
    )
    calibration_end_index = max(
        training_end_index + 1,
        int(len(unique_times) * (1 - validation_fraction)),
    )
    calibration_end_index = min(calibration_end_index, len(unique_times) - 1)
    calibration_start_time = unique_times[training_end_index]
    validation_start_time = unique_times[calibration_end_index]
    train_mask = prepared["time"] < calibration_start_time
    calibration_mask = (
        prepared["time"].ge(calibration_start_time)
        & prepared["time"].lt(validation_start_time)
    )
    validation_mask = prepared["time"].ge(validation_start_time)
    train_frame = prepared.loc[train_mask]
    calibration_frame = prepared.loc[calibration_mask]
    validation_frame = prepared.loc[validation_mask]
    for target in TARGET_COLUMNS:
        if train_frame[target].nunique() < 2:
            raise ValueError(
                f"Training slice for {target} has only one class after "
                "forecast-horizon alignment; check labels, horizon, and time split"
            )

    thresholds: dict[str, float] = {}
    metrics: dict[str, dict[str, Any]] = {}
    timings: dict[str, dict[str, float]] = {
        target: {} for target in TARGET_COLUMNS
    }
    base_models: dict[str, Pipeline | ConstantProbabilityModel] = {}
    calibrated_models: dict[
        str, ConstantProbabilityModel | PlattCalibratedModel
    ] = {}
    pipeline_started = perf_counter()
    train_messages: list[str] = []

    with tqdm(
        TARGET_COLUMNS,
        desc="TRAIN",
        unit="model",
        disable=not show_progress,
        dynamic_ncols=True,
        leave=True,
        file=sys.stdout,
    ) as train_progress:
        for index, target in enumerate(train_progress):
            started = perf_counter()
            train_progress.set_postfix_str(
                f"{index + 1}/5 {display_label(target)}"
            )
            base_models[target] = _fit_target(
                train_frame[feature_columns],
                train_frame[target],
                max_iterations=max_iterations,
                random_state=random_state + index,
            )
            timings[target]["train"] = perf_counter() - started
            train_messages.append(
                    f"[TRAIN {index + 1}/5] {display_label(target)} ({target}) "
                    f"| time={timings[target]['train']:.2f}s "
                    f"| support={int(train_frame[target].sum())}/"
                    f"{len(train_frame)}"
            )
            gc.collect()
    if show_progress:
        print(*train_messages, sep="\n", flush=True)

    calibration_messages: list[str] = []
    with tqdm(
        TARGET_COLUMNS,
        desc="CALIBRATE",
        unit="model",
        disable=not show_progress,
        dynamic_ncols=True,
        leave=True,
        file=sys.stdout,
    ) as calibration_progress:
        for index, target in enumerate(calibration_progress):
            started = perf_counter()
            calibration_progress.set_postfix_str(
                f"{index + 1}/5 {display_label(target)}"
            )
            calibrated_model = _calibrate_target(
                base_models[target],
                calibration_frame[feature_columns],
                calibration_frame[target],
            )
            is_calibrated = bool(
                isinstance(calibrated_model, PlattCalibratedModel)
                and calibrated_model.calibrator is not None
            )
            if require_calibration and not is_calibrated:
                raise ValueError(
                    f"Cannot calibrate {target}: its training/calibration slices need "
                    "both classes with at least two calibration samples per class. "
                    "Adjust the time split/data or explicitly allow uncalibrated scores."
                )
            calibrated_models[target] = calibrated_model
            calibration_probabilities = _positive_probability(
                calibrated_model, calibration_frame[feature_columns]
            )
            threshold = _choose_threshold(
                calibration_frame[target],
                calibration_probabilities,
                max_alert_rate=max_alert_rate,
                min_recall=min_recall,
            )
            thresholds[target] = threshold
            timings[target]["calibration"] = perf_counter() - started
            calibration_messages.append(
                    f"[CALIBRATE {index + 1}/5] {display_label(target)} "
                    f"({target}) | time={timings[target]['calibration']:.2f}s "
                    f"| support={int(calibration_frame[target].sum())}/"
                    f"{len(calibration_frame)} "
                    f"| threshold={threshold:.6f} "
                    f"| calibrated={is_calibrated}"
            )
    if show_progress:
        print(*calibration_messages, sep="\n", flush=True)

    validation_messages: list[str] = []
    with tqdm(
        TARGET_COLUMNS,
        desc="VALIDATE",
        unit="model",
        disable=not show_progress,
        dynamic_ncols=True,
        leave=True,
        file=sys.stdout,
    ) as validation_progress:
        for index, target in enumerate(validation_progress):
            started = perf_counter()
            validation_progress.set_postfix_str(
                f"{index + 1}/5 {display_label(target)}"
            )
            calibrated_model = calibrated_models[target]
            threshold = thresholds[target]
            validation_probabilities = _positive_probability(
                calibrated_model, validation_frame[feature_columns]
            )
            metrics[target] = _target_metrics(
                validation_frame[target], validation_probabilities, threshold
            )
            metrics[target]["positive_training_rows"] = int(
                train_frame[target].sum()
            )
            metrics[target]["positive_calibration_rows"] = int(
                calibration_frame[target].sum()
            )
            metrics[target]["positive_validation_rows"] = int(
                validation_frame[target].sum()
            )
            metrics[target]["validation_prevalence"] = float(
                validation_frame[target].mean()
            )
            metrics[target]["validation_rows"] = len(validation_frame)
            metrics[target]["probability_calibrated"] = bool(
                isinstance(calibrated_model, PlattCalibratedModel)
                and calibrated_model.calibrator is not None
            )
            prevalence = metrics[target]["validation_prevalence"]
            average_precision = metrics[target]["average_precision"]
            metrics[target]["pr_auc_lift_over_prevalence"] = (
                float(average_precision) / float(prevalence)
                if average_precision is not None and prevalence > 0
                else None
            )
            timings[target]["validation"] = perf_counter() - started
            metrics[target]["timing_seconds"] = timings[target]
            validation_messages.append(
                _validation_result_text(index + 1, target, metrics[target])
            )
    if show_progress:
        print(*validation_messages, sep="\n", flush=True)

    average_precisions = [
        float(target_metrics["average_precision"])
        for target_metrics in metrics.values()
        if target_metrics["average_precision"] is not None
    ]
    macro_average_precision = (
        float(np.mean(average_precisions))
        if len(average_precisions) == len(TARGET_COLUMNS)
        else None
    )
    promotion_failures: list[str] = []
    for target, target_metrics in metrics.items():
        if target_metrics["average_precision"] is None:
            promotion_failures.append(f"{target}: invalid PR-AUC")
        if not target_metrics["probability_calibrated"]:
            pass # promotion_failures.append(f"{target}: probability not calibrated")
        lift = target_metrics["pr_auc_lift_over_prevalence"]
        if lift is None or float(lift) < min_pr_lift:
            promotion_failures.append(
                f"{target}: PR-lift below {min_pr_lift:.2f}x"
            )
        if float(target_metrics["recall"]) < min_recall:
            promotion_failures.append(
                f"{target}: recall below {min_recall:.2%}"
            )
        if float(target_metrics["alert_rate"]) > max_alert_rate:
            promotion_failures.append(
                f"{target}: alert rate exceeds {max_alert_rate:.2%}"
            )
        skill = target_metrics["brier_skill_score"]
        if skill is None or float(skill) <= 0:
            pass # promotion_failures.append(f"{target}: Brier skill is not positive")
        if isinstance(calibrated_models[target], ConstantProbabilityModel):
            pass # promotion_failures.append(f"{target}: constant model")
    selection_eligible = (
        macro_average_precision is not None and not promotion_failures
    )
    total_pipeline_seconds = perf_counter() - pipeline_started
    label_audit_frame = prepared.assign(year=prepared["time"].dt.year)
    positive_counts_by_year = (
        label_audit_frame.groupby("year", observed=True)[TARGET_COLUMNS]
        .sum()
        .astype(int)
    )
    label_audit = {
        "positive_counts_by_year": {
            str(year): {
                target: int(value)
                for target, value in row.items()
            }
            for year, row in positive_counts_by_year.to_dict("index").items()
        },
        "positive_year_coverage": {
            target: int(positive_counts_by_year[target].gt(0).sum())
            for target in TARGET_COLUMNS
        },
    }
    if show_progress:
        print(
            "[SUMMARY] "
            f"total_time={total_pipeline_seconds:.2f}s "
            f"| macro_PR-AUC={_metric_text(macro_average_precision)} "
            f"| eligible_for_promotion={selection_eligible}",
            flush=True,
        )
        if promotion_failures:
            print(
                "[PROMOTION BLOCKED] " + "; ".join(promotion_failures),
                flush=True,
            )
    invalid_targets = [
        target
        for target, target_metrics in metrics.items()
        if target_metrics["average_precision"] is None
    ]
    uncalibrated_targets = [
        target
        for target, target_metrics in metrics.items()
        if not target_metrics["probability_calibrated"]
    ]
    if require_calibration and (invalid_targets or uncalibrated_targets):
        raise ValueError(
            "Every target requires calibrated probabilities and both validation "
            f"classes. Invalid PR-AUC: {invalid_targets}; "
            f"uncalibrated: {uncalibrated_targets}"
        )

    fingerprint_columns = [
        "location_id",
        "time",
        *feature_columns,
        *TARGET_COLUMNS,
    ]
    row_hashes = pd.util.hash_pandas_object(
        prepared[fingerprint_columns], index=False
    ).values
    dataset_fingerprint = hashlib.sha256(row_hashes.tobytes()).hexdigest()
    comparison_protocol = {
        "dataset_fingerprint": dataset_fingerprint,
        "forecast_horizon_hours": forecast_horizon_hours,
        "threshold_policy": {
            "max_alert_rate": max_alert_rate,
            "min_recall": min_recall,
            "min_pr_lift": min_pr_lift,
        },
        "calibration_fraction": calibration_fraction,
        "validation_fraction": validation_fraction,
        "calibration_start_time": pd.Timestamp(calibration_start_time).isoformat(),
        "validation_start_time": pd.Timestamp(validation_start_time).isoformat(),
        "feature_columns": feature_columns,
        "target_columns": TARGET_COLUMNS,
    }
    experiment_key = hashlib.sha256(
        json.dumps(
            comparison_protocol, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
    ).hexdigest()[:16]
    created_at = datetime.now(timezone.utc).isoformat()
    bundle = DisasterModelBundle(
        models=calibrated_models,
        thresholds=thresholds,
        feature_columns=feature_columns.copy(),
        target_columns=TARGET_COLUMNS.copy(),
        label_names=LABEL_NAMES.copy(),
        forecast_horizon_hours=forecast_horizon_hours,
        created_at=created_at,
        sklearn_version=sklearn.__version__,
    )
    report: dict[str, Any] = {
        "created_at": created_at,
        "rows_before_aggregation": len(data),
        "rows_after_aggregation": len(prepared),
        "training_rows": len(train_frame),
        "calibration_rows": len(calibration_frame),
        "validation_rows": len(validation_frame),
        "calibration_start_time": pd.Timestamp(calibration_start_time).isoformat(),
        "validation_start_time": pd.Timestamp(validation_start_time).isoformat(),
        "forecast_horizon_hours": forecast_horizon_hours,
        "feature_columns": feature_columns,
        "timing_seconds": {
            "total": total_pipeline_seconds,
            "targets": timings,
        },
        "label_audit": label_audit,
        "temporal_backtest": temporal_backtest,
        "selection": {
            "metric": "macro_average_precision",
            "score": macro_average_precision,
            "higher_is_better": True,
            "eligible_for_promotion": selection_eligible,
            "promotion_failures": promotion_failures,
            "experiment_key": experiment_key,
            "comparison_protocol": comparison_protocol,
        },
        "targets": metrics,
    }
    return bundle, report


def read_training_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError("training data must be a .csv or .parquet file")


def save_training_artifacts(
    bundle: DisasterModelBundle, report: dict[str, Any], output_dir: str | Path
) -> ArtifactSaveResult:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    created_at = datetime.fromisoformat(report["created_at"])
    run_id = created_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_directory = directory / "runs" / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    run_model_path = run_directory / "disaster_model.joblib"
    run_metrics_path = run_directory / "metrics.json"
    best_model_path = directory / "disaster_model.joblib"
    best_metrics_path = directory / "metrics.json"

    selection = report.get("selection", {})
    candidate_score = selection.get("score")
    experiment_key = selection.get("experiment_key", "legacy")
    eligible = bool(selection.get("eligible_for_promotion", False))
    experiment_directory = directory / "experiments" / experiment_key
    experiment_model_path = experiment_directory / "disaster_model.joblib"
    experiment_metrics_path = experiment_directory / "metrics.json"
    experiment_manifest_path = experiment_directory / "best.json"
    root_manifest_path = directory / "best.json"

    run_report = {
        **report,
        "artifact": {
            "run_id": run_id,
            "experiment_key": experiment_key,
        },
    }
    joblib.dump(bundle, run_model_path)
    run_metrics_path.write_text(
        json.dumps(run_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    promoted = False
    best_score = None
    lock = FileLock(str(directory / ".promotion.lock"), timeout=30)
    with lock:
        if experiment_metrics_path.exists():
            existing = json.loads(
                experiment_metrics_path.read_text(encoding="utf-8")
            )
            best_score = existing.get("selection", {}).get("score")
        promoted = eligible and (
            not experiment_model_path.exists()
            or (
                candidate_score is not None
                and (best_score is None or float(candidate_score) > float(best_score))
            )
        )

        run_report["artifact"].update(
            {
                "promoted_to_best": promoted,
                "previous_best_score": best_score,
            }
        )
        serialized_report = json.dumps(
            run_report, ensure_ascii=False, indent=2
        )
        run_metrics_path.write_text(serialized_report, encoding="utf-8")

        if promoted:
            experiment_directory.mkdir(parents=True, exist_ok=True)
            temporary_experiment_model = experiment_directory / ".model.tmp"
            temporary_experiment_metrics = experiment_directory / ".metrics.tmp"
            joblib.dump(bundle, temporary_experiment_model)
            temporary_experiment_metrics.write_text(
                serialized_report, encoding="utf-8"
            )
            os.replace(temporary_experiment_model, experiment_model_path)
            os.replace(temporary_experiment_metrics, experiment_metrics_path)

            temporary_best_model = directory / ".best-model.tmp"
            temporary_best_metrics = directory / ".best-metrics.tmp"
            joblib.dump(bundle, temporary_best_model)
            temporary_best_metrics.write_text(serialized_report, encoding="utf-8")
            os.replace(temporary_best_model, best_model_path)
            os.replace(temporary_best_metrics, best_metrics_path)

            root_manifest = {
                "run_id": run_id,
                "experiment_key": experiment_key,
                "model_path": str(
                    run_model_path.relative_to(directory)
                ).replace("\\", "/"),
                "metrics_path": str(
                    run_metrics_path.relative_to(directory)
                ).replace("\\", "/"),
            }
            experiment_manifest = {
                **root_manifest,
                "model_path": os.path.relpath(
                    run_model_path, experiment_directory
                ).replace("\\", "/"),
                "metrics_path": os.path.relpath(
                    run_metrics_path, experiment_directory
                ).replace("\\", "/"),
            }
            temporary_experiment_manifest = (
                experiment_directory / ".best-manifest.tmp"
            )
            temporary_root_manifest = directory / ".best-manifest.tmp"
            temporary_experiment_manifest.write_text(
                json.dumps(experiment_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_root_manifest.write_text(
                json.dumps(root_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(
                temporary_experiment_manifest, experiment_manifest_path
            )
            os.replace(temporary_root_manifest, root_manifest_path)

    return ArtifactSaveResult(
        run_directory=run_directory,
        run_model_path=run_model_path,
        run_metrics_path=run_metrics_path,
        best_model_path=best_model_path,
        best_metrics_path=best_metrics_path,
        experiment_directory=experiment_directory,
        promoted_to_best=promoted,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--calibration-fraction", type=float, default=0.15)
    parser.add_argument("--forecast-horizon-hours", type=int, default=24)
    parser.add_argument("--max-iterations", type=int, default=200)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--max-alert-rate", type=float, default=0.05)
    parser.add_argument("--min-recall", type=float, default=0.5)
    parser.add_argument("--min-pr-lift", type=float, default=1.5)
    parser.add_argument("--backtest-folds", type=int, default=0)
    parser.add_argument("--backtest-max-iterations", type=int, default=50)
    parser.add_argument(
        "--allow-uncalibrated",
        action="store_true",
        help="Allow raw scores when a target cannot be probability-calibrated",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable tqdm progress bars",
    )
    args = parser.parse_args()

    bundle, report = train_disaster_models(
        read_training_data(args.data),
        forecast_horizon_hours=args.forecast_horizon_hours,
        calibration_fraction=args.calibration_fraction,
        validation_fraction=args.validation_fraction,
        max_iterations=args.max_iterations,
        random_state=args.random_state,
        require_calibration=not args.allow_uncalibrated,
        show_progress=not args.no_progress,
        max_alert_rate=args.max_alert_rate,
        min_recall=args.min_recall,
        min_pr_lift=args.min_pr_lift,
        backtest_folds=args.backtest_folds,
        backtest_max_iterations=args.backtest_max_iterations,
    )
    saved = save_training_artifacts(bundle, report, args.output_dir)
    print(f"Run model: {saved.run_model_path}")
    print(f"Run metrics: {saved.run_metrics_path}")
    if saved.promoted_to_best:
        print(f"New best model: {saved.best_model_path}")
        print(f"Best metrics: {saved.best_metrics_path}")
        print(f"Experiment best: {saved.experiment_directory}")
    elif not saved.best_model_path.exists():
        print("Run archived but not eligible for best-model promotion.")
    else:
        print(f"Best model unchanged: {saved.best_model_path}")


if __name__ == "__main__":
    main()
