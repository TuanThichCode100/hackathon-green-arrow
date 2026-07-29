"""Convert Open-Meteo fields to the feature contract used during training."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


MODEL_FEATURE_COLUMNS = [
    "temperature_2m",
    "dew_point_2m",
    "precipitation",
    "surface_pressure",
    "wind_speed_10m",
    "cloud_cover",
    "wind_gusts_10m",
    "et0_fao_evapotranspiration",
    "soil_temperature_0_to_7cm",
    "soil_temperature_7_to_28cm",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
]

OPEN_METEO_HOURLY_VARIABLES = [
    "temperature_2m",
    "dew_point_2m",
    "precipitation",
    "rain",
    "surface_pressure",
    "wind_speed_10m",
    "cloud_cover",
    "wind_gusts_10m",
    "et0_fao_evapotranspiration",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
]

_DIRECT_MAPPING = {
    column: column
    for column in [
        "temperature_2m",
        "dew_point_2m",
        "precipitation",
        "rain",
        "surface_pressure",
        "wind_speed_10m",
        "cloud_cover",
        "wind_gusts_10m",
        "et0_fao_evapotranspiration",
    ]
}


def _require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"Open-Meteo response is missing hourly fields: {missing}")


def map_open_meteo_hourly_to_model_features(hourly: pd.DataFrame) -> pd.DataFrame:
    """Return numeric model features in the exact order used during training.

    Open-Meteo exposes point soil temperatures and irregular depth bands. The
    training data uses 0-7 cm and 7-28 cm bands, so overlapping moisture layers
    are depth-weighted and temperature point measurements are used as the
    closest available estimates.
    """

    _require_columns(hourly, OPEN_METEO_HOURLY_VARIABLES)
    result = hourly[list(_DIRECT_MAPPING)].rename(columns=_DIRECT_MAPPING).copy()

    result["soil_temperature_0_to_7cm"] = hourly[
        ["soil_temperature_0cm", "soil_temperature_6cm"]
    ].mean(axis=1)
    result["soil_temperature_7_to_28cm"] = hourly["soil_temperature_18cm"]
    result["soil_moisture_0_to_7cm"] = (
        hourly["soil_moisture_0_to_1cm"]
        + 2 * hourly["soil_moisture_1_to_3cm"]
        + 4 * hourly["soil_moisture_3_to_9cm"]
    ) / 7
    result["soil_moisture_7_to_28cm"] = (
        2 * hourly["soil_moisture_3_to_9cm"]
        + 19 * hourly["soil_moisture_9_to_27cm"]
    ) / 21

    result = result[[*MODEL_FEATURE_COLUMNS, "rain"]].apply(
        pd.to_numeric, errors="coerce"
    )
    result = result.replace([np.inf, -np.inf], np.nan)
    return result.astype("float32")
