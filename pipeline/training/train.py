"""Train the five-label natural-disaster probability model."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
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
        if labels.sum() > 0
        else None,
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
    }


def train_disaster_models(
    data: pd.DataFrame,
    *,
    forecast_horizon_hours: int = 24,
    calibration_fraction: float = 0.15,
    validation_fraction: float = 0.2,
    max_iterations: int = 200,
    random_state: int = 42,
    require_calibration: bool = True,
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
    metrics: dict[str, dict[str, float | int | None]] = {}
    calibrated_models: dict[
        str, ConstantProbabilityModel | PlattCalibratedModel
    ] = {}
    for index, target in enumerate(TARGET_COLUMNS):
        base_model = _fit_target(
            train_frame[MODEL_FEATURE_COLUMNS],
            train_frame[target],
            max_iterations=max_iterations,
            random_state=random_state + index,
        )
        calibrated_model = _calibrate_target(
            base_model,
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
        validation_probabilities = _positive_probability(
            calibrated_model, validation_frame[MODEL_FEATURE_COLUMNS]
        )
        metrics[target] = _target_metrics(
            validation_frame[target], validation_probabilities, threshold
        )
        metrics[target]["positive_training_rows"] = int(train_frame[target].sum())
        metrics[target]["positive_calibration_rows"] = int(
            calibration_frame[target].sum()
        )
        metrics[target]["positive_validation_rows"] = int(
            validation_frame[target].sum()
        )
        metrics[target]["probability_calibrated"] = is_calibrated
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
) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "disaster_model.joblib"
    metrics_path = directory / "metrics.json"
    joblib.dump(bundle, model_path)
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return model_path, metrics_path


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
    args = parser.parse_args()

    bundle, report = train_disaster_models(
        read_training_data(args.data),
        forecast_horizon_hours=args.forecast_horizon_hours,
        calibration_fraction=args.calibration_fraction,
        validation_fraction=args.validation_fraction,
        max_iterations=args.max_iterations,
        random_state=args.random_state,
        require_calibration=not args.allow_uncalibrated,
    )
    model_path, metrics_path = save_training_artifacts(
        bundle, report, args.output_dir
    )
    print(f"Model: {model_path}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
