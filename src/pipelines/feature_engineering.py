"""
Turns the clean hourly weather schema (see map_meteo_features.CLEAN_FEATURE_COLUMNS)
into the engineered features described in docs/feature_engineering_plan.md: cyclical
time encodings, multi-day rolling accumulations/extremes for the 72h/168h forecast
horizons, and the domain-specific feature crosses (humidity proxy, net water
retention, landslide trigger index).

Input is expected to already be in the clean schema produced by
map_meteo_features.clean_training_schema() / map_meteo_features.map_meteo_to_training_schema():
one row per (location_id, time), hourly cadence, sorted or not.
"""

from typing import Callable

import numpy as np
import pandas as pd

# snow_depth/snowfall carry ~zero variance for Vietnam's tropical climate (see plan
# Section 1) and are dropped before feature engineering so they don't leak into
# any rolling aggregation by accident.
COLUMNS_TO_DROP = ["snow_depth", "snowfall"]

DAYS_PER_YEAR = 365.25

# Section 3 of the plan: route only the features each disaster model physically
# needs, so unrelated noise doesn't confuse the trees.
FEATURE_ROUTING = {
    "y_lu_lut": [
        "precip_3d_sum",
        "precip_7d_sum",
        "NWR_7d",
        "deep_soil_moisture_3d_avg",
        "month_sin",
        "month_cos",
        "doy_sin",
        "doy_cos",
    ],
    "y_sat_lo": [
        "landslide_trigger_index",
        "NWR_7d",
        "deep_soil_moisture_3d_avg",
        "surface_deep_moisture_delta",
    ],
    "y_dong_loc": [
        "pressure_min_24h",
        "pressure_delta_48h",
        "wind_gust_max_24h",
        "month_sin",
        "month_cos",
        "doy_sin",
        "doy_cos",
    ],
    "y_mua_lon": [
        "temp_dew_spread_min_24h",
        "precip_3d_sum",
        "cloud_cover_max_24h",
        "pressure_min_24h",
    ],
    "y_mua_da": [
        "temp_dew_spread_min_24h",
        "temperature_min_24h",
        "temperature_max_24h",
        "wind_gust_max_24h",
        "pressure_delta_48h",
    ],
}


def add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add month_sin/cos and doy_sin/cos so the model sees December as adjacent
    to January instead of far away (Step A of the plan).
    """
    df = df.copy()
    time = pd.to_datetime(df["time"])
    month = time.dt.month
    day_of_year = time.dt.dayofyear

    df["month_sin"] = np.sin(2 * np.pi * month / 12)
    df["month_cos"] = np.cos(2 * np.pi * month / 12)
    df["doy_sin"] = np.sin(2 * np.pi * day_of_year / DAYS_PER_YEAR)
    df["doy_cos"] = np.cos(2 * np.pi * day_of_year / DAYS_PER_YEAR)
    return df


def _time_rolling(df: pd.DataFrame, value_col: str, window: str, func: str | Callable) -> np.ndarray:
    """Rolling aggregation of `value_col` over a time-based `window` (e.g. "72h"),
    computed independently per location_id.

    Requires `df` to already be sorted by ["location_id", "time"].
    """
    result = pd.Series(index=df.index, dtype="float64")
    for _, group in df.groupby("location_id"):
        result.loc[group.index] = group.set_index("time")[value_col].rolling(window).agg(func).to_numpy()
    return result.to_numpy()


def add_rolling_aggregations(df: pd.DataFrame) -> pd.DataFrame:
    """Add the Step B forecast aggregations: hydrological accumulations, soil
    state averages, and atmospheric extremes over the 24h/72h/168h windows.

    Assumes `df` is sorted by ["location_id", "time"].
    """
    df = df.copy()

    df["precip_3d_sum"] = _time_rolling(df, "precipitation", "72h", "sum")
    df["precip_7d_sum"] = _time_rolling(df, "precipitation", "168h", "sum")
    df["evapo_3d_sum"] = _time_rolling(df, "et0_fao_evapotranspiration", "72h", "sum")
    df["evapo_7d_sum"] = _time_rolling(df, "et0_fao_evapotranspiration", "168h", "sum")

    df["deep_soil_moisture_3d_avg"] = _time_rolling(df, "soil_moisture_7_to_28cm", "72h", "mean")

    df["wind_gust_max_24h"] = _time_rolling(df, "wind_gusts_10m", "24h", "max")
    df["pressure_min_24h"] = _time_rolling(df, "surface_pressure", "24h", "min")
    df["cloud_cover_max_24h"] = _time_rolling(df, "cloud_cover", "24h", "max")
    df["temperature_min_24h"] = _time_rolling(df, "temperature_2m", "24h", "min")
    df["temperature_max_24h"] = _time_rolling(df, "temperature_2m", "24h", "max")

    # Pressure trend/velocity: Day-3 vs Day-1 24h-minimum pressure, 48h apart.
    # Assumes hourly cadence (as produced by preprocess.fetch_meteo_data), so a
    # 48-row shift approximates 48h.
    df["pressure_delta_48h"] = df.groupby("location_id")["pressure_min_24h"].transform(
        lambda s: s - s.shift(48)
    )
    return df


def add_domain_crosses(df: pd.DataFrame) -> pd.DataFrame:
    """Add the Step C domain-specific feature crosses: humidity proxy, net water
    retention, landslide trigger index, and the surface/deep moisture delta.

    Assumes `df` already has the Step B rolling aggregations (NWR_7d and the
    landslide trigger index depend on precip_7d_sum/evapo_7d_sum and
    deep_soil_moisture_3d_avg).
    """
    df = df.copy()

    df["temp_dew_spread"] = df["temperature_2m"] - df["dew_point_2m"]
    df["temp_dew_spread_min_24h"] = _time_rolling(df, "temp_dew_spread", "24h", "min")

    df["NWR_7d"] = df["precip_7d_sum"] - df["evapo_7d_sum"]
    df["landslide_trigger_index"] = df["NWR_7d"] * df["deep_soil_moisture_3d_avg"]
    df["surface_deep_moisture_delta"] = df["soil_moisture_0_to_7cm"] - df["soil_moisture_7_to_28cm"]
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full feature engineering pipeline from docs/feature_engineering_plan.md
    on a clean hourly weather dataframe (location_id, time, + weather columns).
    """
    df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(["location_id", "time"]).reset_index(drop=True)

    df = add_cyclical_time_features(df)
    df = add_rolling_aggregations(df)
    df = add_domain_crosses(df)
    return df


def get_routed_features(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Select location_id/time plus only the engineered features routed to `target`
    (see FEATURE_ROUTING / plan Section 3)."""
    if target not in FEATURE_ROUTING:
        raise ValueError(f"Unknown target '{target}'. Expected one of {list(FEATURE_ROUTING)}")
    columns = ["location_id", "time"] + FEATURE_ROUTING[target]
    return df[columns]


if __name__ == "__main__":
    from map_meteo_features import clean_training_schema

    training_df = pd.read_csv("data/weather_merged_2021_2026_labeled.csv")
    cleaned = clean_training_schema(training_df)
    engineered = engineer_features(cleaned)
    engineered.to_csv("data/weather_features_engineered.csv", index=False)
    print(f"Wrote {len(engineered)} rows to data/weather_features_engineered.csv")
