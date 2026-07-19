"""
Unifies the raw Open-Meteo hourly schema (hourly_weather_meteo_data.csv) and the
training data schema (df_sample.csv / weather_merged_2021_2026_labeled.csv) onto a
single clean column-naming convention, so meteo pulls can be fed straight into the
training pipeline without column names that break libraries expecting valid
identifiers (parentheses, "°", "³", "%", etc.).

Units are dropped from column names and tracked separately in FEATURE_UNITS instead.

See docs/meteo_feature_mapping.md for the rationale behind each mapping decision.
"""

import re

import pandas as pd

# Canonical clean feature columns the training pipeline should consume, plus the unit
# each one is expressed in. This is the single naming convention both the meteo pull
# and the training data get normalized to.
FEATURE_UNITS = {
    "location_id": None,
    "time": None,
    "temperature_2m": "°C",
    "dew_point_2m": "°C",
    "precipitation": "mm",
    "surface_pressure": "hPa",
    "wind_speed_10m": "km/h",
    "cloud_cover": "%",
    "rain": "mm",
    "snow_depth": "m",
    "snowfall": "cm",
    "wind_gusts_10m": "km/h",
    "et0_fao_evapotranspiration": "mm",
    "soil_temperature_0_to_7cm": "°C",
    "soil_temperature_7_to_28cm": "°C",
    "soil_moisture_0_to_7cm": "m³/m³",
    "soil_moisture_7_to_28cm": "m³/m³",
}

CLEAN_FEATURE_COLUMNS = list(FEATURE_UNITS.keys())

# Label columns present in the training data only (not weather features).
TRAINING_LABEL_COLUMNS = ["y_mua_lon", "y_sat_lo", "y_dong_loc", "y_mua_da", "y_lu_lut"]

# Meteo columns that map 1:1 onto a clean feature column (same physical quantity, same unit).
METEO_TO_CLEAN_DIRECT_RENAME = {
    "date": "time",
    "temperature_2m": "temperature_2m",
    "dew_point_2m": "dew_point_2m",
    "precipitation": "precipitation",
    "surface_pressure": "surface_pressure",
    "cloud_cover": "cloud_cover",
    "snow_depth": "snow_depth",
    "snowfall": "snowfall",
    "wind_gusts_10m": "wind_gusts_10m",
}

# Matches the " (unit)" suffix on the raw training columns, e.g. "temperature_2m (°C)".
_UNIT_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")


def clean_column_name(raw_col: str) -> str:
    """Strip a training-data column's "(unit)" suffix, e.g. "precipitation (mm)" -> "precipitation"."""
    return _UNIT_SUFFIX_RE.sub("", raw_col).strip()


def clean_training_schema(training_df: pd.DataFrame) -> pd.DataFrame:
    """Rename a raw training-data dataframe's columns to the clean naming convention
    (drops the "(unit)" suffixes; label columns pass through unchanged).
    """
    df = training_df.rename(columns=clean_column_name)
    ordered = [c for c in CLEAN_FEATURE_COLUMNS + TRAINING_LABEL_COLUMNS if c in df.columns]
    return df[ordered]


def map_meteo_to_training_schema(meteo_df: pd.DataFrame, location_id=None) -> pd.DataFrame:
    """Transform a raw Open-Meteo hourly dataframe into the clean training feature schema.

    `meteo_df` is expected to have the columns produced by
    notebook/get_meteo_data.ipynb / src/pipelines/preprocess.py.
    """
    df = meteo_df.copy()
    out = pd.DataFrame(index=df.index)

    out["location_id"] = location_id
    for src_col, dst_col in METEO_TO_CLEAN_DIRECT_RENAME.items():
        out[dst_col] = df[src_col]

    # rain: Open-Meteo defines precipitation = rain + showers + snowfall(water equiv).
    # The meteo pull didn't request "rain" directly, so it's backed out from what was requested.
    out["rain"] = (df["precipitation"] - df["showers"]).clip(lower=0)

    # wind_speed_10m: never requested by the meteo pull (only wind_gusts_10m was).
    # Gusts are not a valid substitute for mean wind speed, so leave this missing
    # until the API call is updated to also request "wind_speed_10m".
    out["wind_speed_10m"] = pd.NA

    # et0_fao_evapotranspiration: the meteo pull requested "evapotranspiration", which is a
    # different Open-Meteo variable (FAO-56 reference ET has its own "et0_fao_evapotranspiration"
    # parameter). Used here as an approximation only.
    out["et0_fao_evapotranspiration"] = df["evapotranspiration"]

    # Soil layers: the meteo pull used point-depth variables (0/6/18cm) instead of the
    # depth-band variables the training data uses (0-7cm / 7-28cm). Approximate the bands
    # by averaging the point depths that fall inside (or nearest to) each band.
    out["soil_temperature_0_to_7cm"] = df[["soil_temperature_0cm", "soil_temperature_6cm"]].mean(axis=1)
    out["soil_temperature_7_to_28cm"] = df[["soil_temperature_6cm", "soil_temperature_18cm"]].mean(axis=1)
    out["soil_moisture_0_to_7cm"] = df[
        ["soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm"]
    ].mean(axis=1)
    out["soil_moisture_7_to_28cm"] = df["soil_moisture_9_to_27cm"]

    return out[CLEAN_FEATURE_COLUMNS]


# Feature set consumed at inference time (see src/pipelines/preprocess.py's
# fetch_meteo_data()). "location" replaces "location_id" (looked up by name,
# not id) and snow_depth/snowfall are dropped since they aren't requested from
# the API for this pipeline.
INFERENCE_FEATURE_COLUMNS = [
    "location",
    "time",
    "temperature_2m",
    "dew_point_2m",
    "rain",
    "precipitation",
    "wind_speed_10m",
    "wind_gusts_10m",
    "et0_fao_evapotranspiration",
    "soil_temperature_0_to_7cm",
    "soil_temperature_7_to_28cm",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "cloud_cover",
    "surface_pressure",
]


def map_meteo_to_inference_schema(meteo_df: pd.DataFrame) -> pd.DataFrame:
    """Map a fetch_meteo_data() pull (src/pipelines/preprocess.py) onto the
    INFERENCE_FEATURE_COLUMNS schema.

    Unlike map_meteo_to_training_schema(), no renaming or approximation is
    needed here: fetch_meteo_data() already requests Open-Meteo's hourly
    variables under the training-matching names (see HOURLY_VARIABLES in
    preprocess.py and docs/meteo_feature_mapping.md), so this just renames
    "date" -> "time" and orders/selects the expected columns.
    """
    df = meteo_df.rename(columns={"date": "time"})
    missing = [c for c in INFERENCE_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"meteo_df is missing expected columns: {missing}")
    return df[INFERENCE_FEATURE_COLUMNS]


if __name__ == "__main__":
    training_df = pd.read_csv("data/weather_merged_2021_2026_labeled.csv")
    cleaned = clean_training_schema(training_df)
    cleaned.to_csv("data/weather_merged_2021_2026_clean.csv", index=False)
    print(f"Wrote {len(cleaned)} rows to data/weather_merged_2021_2026_clean.csv")

    units_df = pd.DataFrame(
        [{"feature": k, "unit": v} for k, v in FEATURE_UNITS.items() if v is not None]
    )
    units_df.to_csv("data/feature_units.csv", index=False)
    print(f"Wrote {len(units_df)} unit entries to data/feature_units.csv")
