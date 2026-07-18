"""Open-Meteo forecast ingestion and preprocessing pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline.shared.meteo_feature_mapping import (
    MODEL_FEATURE_COLUMNS,
    OPEN_METEO_HOURLY_VARIABLES,
    map_open_meteo_hourly_to_model_features,
)


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def preprocess_open_meteo_response(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert one Open-Meteo JSON response to timestamped model input."""

    if "hourly" not in payload or "time" not in payload["hourly"]:
        raise ValueError("Open-Meteo response does not contain hourly.time")

    hourly = pd.DataFrame(payload["hourly"])
    features = map_open_meteo_hourly_to_model_features(hourly)
    timezone_name = payload.get("timezone")
    timestamps = pd.to_datetime(hourly["time"], errors="raise")
    if timezone_name:
        if timestamps.dt.tz is None:
            timestamps = timestamps.dt.tz_localize(
                timezone_name, ambiguous="infer", nonexistent="shift_forward"
            )
        else:
            timestamps = timestamps.dt.tz_convert(timezone_name)
    identity = pd.DataFrame(
        {
            "time": timestamps,
            "latitude": float(payload["latitude"]),
            "longitude": float(payload["longitude"]),
        }
    )
    return pd.concat([identity, features], axis=1)[
        ["time", "latitude", "longitude", *MODEL_FEATURE_COLUMNS]
    ]


def _retrying_session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_open_meteo_forecast(
    latitude: float,
    longitude: float,
    *,
    forecast_days: int = 7,
    timezone: str = "Asia/Bangkok",
    timeout_seconds: float = 30,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch an hourly forecast and return data ready for model inference."""

    if not 1 <= forecast_days <= 16:
        raise ValueError("forecast_days must be between 1 and 16")

    client = session or _retrying_session()
    response = client.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(OPEN_METEO_HOURLY_VARIABLES),
            "forecast_days": forecast_days,
            "timezone": timezone,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return preprocess_open_meteo_response(response.json())


def write_preprocessed_data(data: pd.DataFrame, output_path: str | Path) -> Path:
    """Write preprocessed data as CSV or Parquet based on the file suffix."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".parquet":
        data.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        data.to_csv(path, index=False)
    else:
        raise ValueError("output path must end with .csv or .parquet")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Open-Meteo data and convert it to the model schema."
    )
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--forecast-days", type=int, default=7)
    parser.add_argument("--timezone", default="Asia/Bangkok")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = fetch_open_meteo_forecast(
        args.latitude,
        args.longitude,
        forecast_days=args.forecast_days,
        timezone=args.timezone,
    )
    path = write_preprocessed_data(data, args.output)
    print(f"Wrote {len(data)} hourly rows to {path}")


if __name__ == "__main__":
    main()
