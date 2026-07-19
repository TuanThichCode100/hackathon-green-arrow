"""Run disaster probability inference from preprocessed or live Meteo data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from pipeline.preprocessing.open_meteo import fetch_open_meteo_forecast
from pipeline.shared.model_bundle import DisasterModelBundle


IDENTITY_COLUMNS = ["time", "latitude", "longitude"]


def load_model(path: str | Path) -> DisasterModelBundle:
    model_path = Path(path)
    manifest_path = model_path.parent / "best.json"
    if model_path.name == "disaster_model.joblib" and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        model_path = model_path.parent / manifest["model_path"]
    model = joblib.load(model_path)
    if not isinstance(model, DisasterModelBundle):
        raise TypeError("Artifact is not a DisasterModelBundle")
    return model


def predict_hazards(
    model: DisasterModelBundle, model_input: pd.DataFrame
) -> list[dict[str, Any]]:
    """Return one structured five-hazard probability forecast per input row."""

    missing_identity = sorted(set(IDENTITY_COLUMNS).difference(model_input.columns))
    if missing_identity:
        raise ValueError(f"Inference input is missing identity columns: {missing_identity}")

    rows = model_input.reset_index(drop=True)
    probabilities = model.predict_proba(rows).reset_index(drop=True)
    records: list[dict[str, Any]] = []
    for position, row in rows.iterrows():
        timestamp = pd.Timestamp(row["time"])
        forecast_time = timestamp + pd.Timedelta(
            hours=model.forecast_horizon_hours
        )
        hazards = []
        for target in model.target_columns:
            probability = float(probabilities.iloc[position][target])
            threshold = float(model.thresholds[target])
            hazards.append(
                {
                    "code": target,
                    "name": model.label_names[target],
                    "probability": probability,
                    "probability_percent": probability * 100,
                    "probability_calibrated": model.probability_is_calibrated(
                        target
                    ),
                    "threshold": threshold,
                    "predicted": bool(probability >= threshold),
                }
            )
        records.append(
            {
                "feature_time": timestamp.isoformat(),
                "forecast_time": forecast_time.isoformat(),
                "forecast_horizon_hours": model.forecast_horizon_hours,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "hazards": hazards,
            }
        )
    return records


def run_open_meteo_inference(
    model: DisasterModelBundle,
    latitude: float,
    longitude: float,
    *,
    forecast_days: int = 7,
    history_hours: int = 168,
    timezone: str = "Asia/Bangkok",
) -> list[dict[str, Any]]:
    model_input = fetch_open_meteo_forecast(
        latitude,
        longitude,
        forecast_days=forecast_days,
        history_hours=history_hours,
        timezone=timezone,
    )
    return predict_hazards(model, model_input)


def read_preprocessed_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, parse_dates=["time"])
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError("inference input must be a .csv or .parquet file")


def write_predictions(predictions: list[dict[str, Any]], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Preprocessed CSV/Parquet input")
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--forecast-days", type=int, default=7)
    parser.add_argument("--history-hours", type=int, default=168)
    parser.add_argument("--timezone", default="Asia/Bangkok")
    parser.add_argument("--output", type=Path, default=Path("predictions.json"))
    args = parser.parse_args()

    model = load_model(args.model)
    if args.input:
        predictions = predict_hazards(model, read_preprocessed_data(args.input))
    else:
        if args.latitude is None or args.longitude is None:
            parser.error("provide --input or both --latitude and --longitude")
        predictions = run_open_meteo_inference(
            model,
            args.latitude,
            args.longitude,
            forecast_days=args.forecast_days,
            history_hours=args.history_hours,
            timezone=args.timezone,
        )
    output = write_predictions(predictions, args.output)
    print(f"Wrote {len(predictions)} hourly predictions to {output}")


if __name__ == "__main__":
    main()
