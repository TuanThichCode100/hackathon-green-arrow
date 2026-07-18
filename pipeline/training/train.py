"""Train the five-label natural-disaster probability model."""

from __future__ import annotations

import argparse
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from tqdm.auto import tqdm

from pipeline.shared.meteo_feature_mapping import MODEL_FEATURE_COLUMNS
from pipeline.shared.model_bundle import (
    ConstantProbabilityModel,
    DisasterModelBundle,
    PlattCalibratedModel,
)


TARGET_COLUMNS = [
    "y_mua_lon",
    "y_sat_lo",
    "y_dong_loc",
    "y_mua_da",
    "y_lu_lut",
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
    normalized_columns = [
        str(column).replace("Â°", "°").replace("Â³", "³") for column in data.columns
    ]
    if len(normalized_columns) != len(set(normalized_columns)):
        raise ValueError("Training data has duplicate columns after encoding cleanup")
    data = data.rename(columns=dict(zip(data.columns, normalized_columns)))

    required = {"location_id", "time", *MODEL_FEATURE_COLUMNS, *TARGET_COLUMNS}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Training data is missing columns: {missing}")

    frame = data[list(required)].copy()
    frame["time"] = pd.to_datetime(frame["time"], errors="raise")
    frame[MODEL_FEATURE_COLUMNS] = frame[MODEL_FEATURE_COLUMNS].apply(
        pd.to_numeric, errors="coerce"
    )
    if frame[MODEL_FEATURE_COLUMNS].isna().all(axis=0).any():
        empty = frame[MODEL_FEATURE_COLUMNS].columns[
            frame[MODEL_FEATURE_COLUMNS].isna().all(axis=0)
        ].tolist()
        raise ValueError(f"Training features contain no numeric values: {empty}")

    for target in TARGET_COLUMNS:
        numeric = pd.to_numeric(frame[target], errors="coerce")
        if numeric.isna().any():
            raise ValueError(f"Target {target} contains missing/non-numeric values")
        frame[target] = numeric.ne(0).astype("int8")

    weather = (
        frame.groupby(["location_id", "time"], as_index=False, observed=True)[
            MODEL_FEATURE_COLUMNS
        ]
        .mean()
    )
    targets = (
        frame.groupby(["location_id", "time"], as_index=False, observed=True)[
            TARGET_COLUMNS
        ]
        .max()
    )
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


def _new_classifier(max_iterations: int, random_state: int) -> Pipeline:
    return Pipeline(
        [
            (
                "classifier",
                HistGradientBoostingClassifier(
                    max_iter=max_iterations,
                    max_leaf_nodes=31,
                    learning_rate=0.08,
                    l2_regularization=1.0,
                    class_weight="balanced",
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
    model = _new_classifier(max_iterations, random_state)
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


def _choose_threshold(labels: pd.Series, probabilities: np.ndarray) -> float:
    if labels.sum() == 0:
        return 0.5
    candidates = np.linspace(0.05, 0.95, 19)
    scores = [f1_score(labels, probabilities >= value, zero_division=0) for value in candidates]
    return float(candidates[int(np.argmax(scores))])


def _target_metrics(
    labels: pd.Series, probabilities: np.ndarray, threshold: float
) -> dict[str, float | int | None]:
    predictions = probabilities >= threshold
    has_both_classes = labels.nunique() == 2
    return {
        "threshold": threshold,
        "roc_auc": float(roc_auc_score(labels, probabilities))
        if has_both_classes
        else None,
        "average_precision": float(average_precision_score(labels, probabilities))
        if has_both_classes
        else None,
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
    }


def _metric_text(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def _display_label(target: str) -> str:
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
        f"[VALIDATE {index}/{len(TARGET_COLUMNS)}] {_display_label(target)} "
        f"({target}) | time={metrics['timing_seconds']['validation']:.2f}s "
        f"| support={metrics['positive_validation_rows']}/"
        f"{metrics['validation_rows']} "
        f"| prevalence={metrics['validation_prevalence']:.6f} "
        f"| PR-AUC={_metric_text(metrics['average_precision'])} "
        f"| PR-lift={_metric_text(metrics['pr_auc_lift_over_prevalence'], 2)}x "
        f"| ROC-AUC={_metric_text(metrics['roc_auc'])} "
        f"| Brier={_metric_text(metrics['brier_score'], 6)} "
        f"| precision={_metric_text(metrics['precision'])} "
        f"| recall={_metric_text(metrics['recall'])} "
        f"| F1={_metric_text(metrics['f1'])} "
        f"| threshold={_metric_text(metrics['threshold'], 2)} "
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

    prepared = prepare_training_data(
        data, forecast_horizon_hours=forecast_horizon_hours
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
                f"{index + 1}/5 {_display_label(target)}"
            )
            base_models[target] = _fit_target(
                train_frame[MODEL_FEATURE_COLUMNS],
                train_frame[target],
                max_iterations=max_iterations,
                random_state=random_state + index,
            )
            timings[target]["train"] = perf_counter() - started
            train_messages.append(
                    f"[TRAIN {index + 1}/5] {_display_label(target)} ({target}) "
                    f"| time={timings[target]['train']:.2f}s "
                    f"| support={int(train_frame[target].sum())}/"
                    f"{len(train_frame)}"
            )
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
                f"{index + 1}/5 {_display_label(target)}"
            )
            calibrated_model = _calibrate_target(
                base_models[target],
                calibration_frame[MODEL_FEATURE_COLUMNS],
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
                calibrated_model, calibration_frame[MODEL_FEATURE_COLUMNS]
            )
            threshold = _choose_threshold(
                calibration_frame[target], calibration_probabilities
            )
            thresholds[target] = threshold
            timings[target]["calibration"] = perf_counter() - started
            calibration_messages.append(
                    f"[CALIBRATE {index + 1}/5] {_display_label(target)} "
                    f"({target}) | time={timings[target]['calibration']:.2f}s "
                    f"| support={int(calibration_frame[target].sum())}/"
                    f"{len(calibration_frame)} "
                    f"| threshold={threshold:.2f} "
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
                f"{index + 1}/5 {_display_label(target)}"
            )
            calibrated_model = calibrated_models[target]
            threshold = thresholds[target]
            validation_probabilities = _positive_probability(
                calibrated_model, validation_frame[MODEL_FEATURE_COLUMNS]
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
    selection_eligible = macro_average_precision is not None
    total_pipeline_seconds = perf_counter() - pipeline_started
    if show_progress:
        print(
            "[SUMMARY] "
            f"total_time={total_pipeline_seconds:.2f}s "
            f"| macro_PR-AUC={_metric_text(macro_average_precision)} "
            f"| eligible_for_promotion={selection_eligible}",
            flush=True,
        )
    if require_calibration and not selection_eligible:
        invalid_targets = [
            target
            for target, target_metrics in metrics.items()
            if target_metrics["average_precision"] is None
        ]
        raise ValueError(
            "Validation must contain both classes for every target before model "
            f"selection. Invalid targets: {invalid_targets}"
        )

    fingerprint_columns = [
        "location_id",
        "time",
        *MODEL_FEATURE_COLUMNS,
        *TARGET_COLUMNS,
    ]
    row_hashes = pd.util.hash_pandas_object(
        prepared[fingerprint_columns], index=False
    ).values
    dataset_fingerprint = hashlib.sha256(row_hashes.tobytes()).hexdigest()
    comparison_protocol = {
        "dataset_fingerprint": dataset_fingerprint,
        "forecast_horizon_hours": forecast_horizon_hours,
        "calibration_fraction": calibration_fraction,
        "validation_fraction": validation_fraction,
        "calibration_start_time": pd.Timestamp(calibration_start_time).isoformat(),
        "validation_start_time": pd.Timestamp(validation_start_time).isoformat(),
        "feature_columns": MODEL_FEATURE_COLUMNS,
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
        feature_columns=MODEL_FEATURE_COLUMNS.copy(),
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
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "timing_seconds": {
            "total": total_pipeline_seconds,
            "targets": timings,
        },
        "selection": {
            "metric": "macro_average_precision",
            "score": macro_average_precision,
            "higher_is_better": True,
            "eligible_for_promotion": selection_eligible,
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
