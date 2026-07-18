"""Stable, serializable model artifact types.

These classes live outside CLI modules so artifacts created with ``python -m``
can be loaded safely by a different process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ConstantProbabilityModel:
    """Probability model used when a target has only one observed class."""

    probability: float

    def positive_probability(self, rows: int) -> np.ndarray:
        return np.full(rows, self.probability, dtype=float)


@dataclass
class PlattCalibratedModel:
    """Binary classifier with an optional held-out Platt probability calibrator."""

    base_model: Any
    calibrator: Any | None

    def positive_probability(self, features: pd.DataFrame) -> np.ndarray:
        classes = self.base_model.named_steps["classifier"].classes_.tolist()
        raw = self.base_model.predict_proba(features)[:, classes.index(1)]
        if self.calibrator is None:
            return raw
        clipped = np.clip(raw, 1e-7, 1 - 1e-7)
        logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
        return self.calibrator.predict_proba(logits)[:, 1]


@dataclass
class DisasterModelBundle:
    """Serializable model artifact shared by training and inference."""

    models: dict[str, Any]
    thresholds: dict[str, float]
    feature_columns: list[str]
    target_columns: list[str]
    label_names: dict[str, str]
    forecast_horizon_hours: int
    created_at: str
    sklearn_version: str

    def probability_is_calibrated(self, target: str) -> bool:
        model = self.models[target]
        return bool(
            isinstance(model, PlattCalibratedModel)
            and model.calibrator is not None
        )

    def predict_proba(self, features: pd.DataFrame) -> pd.DataFrame:
        missing = sorted(set(self.feature_columns).difference(features.columns))
        if missing:
            raise ValueError(f"Model input is missing features: {missing}")
        matrix = features[self.feature_columns].apply(pd.to_numeric, errors="coerce")
        output: dict[str, np.ndarray] = {}
        for target in self.target_columns:
            model = self.models[target]
            if isinstance(model, ConstantProbabilityModel):
                output[target] = model.positive_probability(len(matrix))
                continue
            output[target] = model.positive_probability(matrix)
        return pd.DataFrame(output, index=features.index)

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        probabilities = self.predict_proba(features)
        return pd.DataFrame(
            {
                target: probabilities[target].ge(self.thresholds[target]).astype("int8")
                for target in self.target_columns
            },
            index=features.index,
        )
