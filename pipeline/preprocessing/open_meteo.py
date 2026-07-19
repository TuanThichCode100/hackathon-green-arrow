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
    OPEN_METEO_HOURLY_VARIABLES,
    map_open_meteo_hourly_to_model_features,
)
from weather_data.build_weather_features import build_weather_features


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
LEGACY_FEATURE_ALIASES = {
    "temperature_2m": "temperature_2m (°C)",
    "dew_point_2m": "dew_point_2m (°C)",
    "precipitation": "precipitation (mm)",
    "surface_pressure": "surface_pressure (hPa)",
    "wind_speed_10m": "wind_speed_10m (km/h)",
    "cloud_cover": "cloud_cover (%)",
    "wind_gusts_10m": "wind_gusts_10m (km/h)",
    "et0_fao_evapotranspiration": "et0_fao_evapotranspiration (mm)",
    "soil_temperature_0_to_7cm": "soil_temperature_0_to_7cm (°C)",
    "soil_temperature_7_to_28cm": "soil_temperature_7_to_28cm (°C)",
    "soil_moisture_0_to_7cm": "soil_moisture_0_to_7cm (m³/m³)",
    "soil_moisture_7_to_28cm": "soil_moisture_7_to_28cm (m³/m³)",
}


def preprocess_open_meteo_response(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert one Open-Meteo JSON response to timestamped model input."""

    if "hourly" not in payload or "time" not in payload["hourly"]:
        raise ValueError("Open-Meteo response does not contain hourly.time")

    hourly = pd.DataFrame(payload["hourly"])
    base_features = map_open_meteo_hourly_to_model_features(hourly)
    timezone_name = payload.get("timezone")
    timestamps = pd.to_datetime(hourly["time"], errors="raise")
    if timezone_name:
        if timestamps.dt.tz is None:
            timestamps = timestamps.dt.tz_localize(
                timezone_name, ambiguous="infer", nonexistent="shift_forward"
            )
        else:
            timestamps = timestamps.dt.tz_convert(timezone_name)
    feature_source = pd.concat(
        [
            pd.DataFrame({"location_id": 0, "time": timestamps}),
            base_features,
        ],
        axis=1,
    )
    features = build_weather_features(feature_source, show_progress=False).drop(
        columns=["location_id", "time"]
    )
    for canonical, legacy in LEGACY_FEATURE_ALIASES.items():
        features[legacy] = features[canonical]
    identity = pd.DataFrame(
        {
            "time": timestamps,
            "latitude": float(payload["latitude"]),
            "longitude": float(payload["longitude"]),
        }
    )
    return pd.concat([identity, features], axis=1)


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
    history_hours: int = 168,
    timezone: str = "Asia/Bangkok",
    timeout_seconds: float = 30,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch an hourly forecast and return data ready for model inference."""

    if not 1 <= forecast_days <= 16:
        raise ValueError("forecast_days must be between 1 and 16")
    if history_hours < 168:
        raise ValueError("history_hours must be at least 168 for model features")

    client = session or _retrying_session()
    response = client.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(OPEN_METEO_HOURLY_VARIABLES),
            "forecast_days": forecast_days,
            "past_hours": history_hours,
            "current": "temperature_2m",
            "timezone": timezone,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    prepared = preprocess_open_meteo_response(payload)
    current_time = payload.get("current", {}).get("time")
    if current_time is not None:
        boundary = pd.Timestamp(current_time)
        prepared_time = pd.to_datetime(prepared["time"])
        if prepared_time.dt.tz is not None and boundary.tzinfo is None:
            matching = prepared_time[
                prepared_time.dt.tz_localize(None).eq(boundary)
            ]
            boundary = (
                matching.iloc[0]
                if not matching.empty
                else boundary.tz_localize(prepared_time.dt.tz, ambiguous=False)
            )
        prepared = prepared.loc[prepared_time.ge(boundary)].reset_index(drop=True)
        if prepared.empty:
            raise ValueError("Open-Meteo response has no rows at or after current.time")
        return prepared

    forecast_rows = forecast_days * 24
    if len(prepared) < forecast_rows:
        raise ValueError("Open-Meteo response contains fewer forecast rows than expected")
    return prepared.tail(forecast_rows).reset_index(drop=True)


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
    parser.add_argument("--history-hours", type=int, default=168)
    parser.add_argument("--timezone", default="Asia/Bangkok")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = fetch_open_meteo_forecast(
        args.latitude,
        args.longitude,
        forecast_days=args.forecast_days,
        history_hours=args.history_hours,
        timezone=args.timezone,
    )
    path = write_preprocessed_data(data, args.output)
    print(f"Wrote {len(data)} hourly rows to {path}")


if __name__ == "__main__":
    main()
