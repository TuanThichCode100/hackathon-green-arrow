"""
Fetches Open-Meteo hourly weather data for named locations, using the lat/lon
lookup table in data/maping_location.csv.

The hourly variables requested (HOURLY_VARIABLES) are chosen to match the
training feature schema names directly -- see docs/meteo_feature_mapping.md
and src/pipelines/map_meteo_features.py for how this feeds into training.
"""

from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LOCATION_MAPPING_PATH = Path(__file__).resolve().parents[2] / "data" / "maping_location.csv"

# Requested directly under these names because Open-Meteo exposes them 1:1 with
# the training feature schema (confirmed against the live API), so no renaming
# or approximation is needed downstream in map_meteo_features.py.
HOURLY_VARIABLES = [
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

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def load_location_mapping(mapping_path: Path = LOCATION_MAPPING_PATH) -> pd.DataFrame:
    """Load the commune name -> lat/lon lookup table."""
    return pd.read_csv(mapping_path)


def get_location_coordinates(
    location_name: str,
    mapping_df: pd.DataFrame | None = None,
    mapping_path: Path = LOCATION_MAPPING_PATH,
) -> tuple[float, float]:
    """Look up (latitude, longitude) for a commune name in maping_location.csv."""
    if mapping_df is None:
        mapping_df = load_location_mapping(mapping_path)

    normalized = location_name.strip().casefold()
    match = mapping_df[mapping_df["commune_name"].str.strip().str.casefold() == normalized]
    if match.empty:
        raise ValueError(f"Location '{location_name}' not found in {mapping_path}")

    row = match.iloc[0]
    return float(row["latitude"]), float(row["longitude"])


def fetch_meteo_data(
    location_name: str,
    past_days: int = 30,
    forecast_days: int | None = None,
    mapping_df: pd.DataFrame | None = None,
    mapping_path: Path = LOCATION_MAPPING_PATH,
) -> pd.DataFrame:
    """Fetch hourly Open-Meteo data for a named location.

    Looks up `location_name`'s lat/lon from maping_location.csv, calls the
    Open-Meteo forecast API for HOURLY_VARIABLES, and returns a dataframe with
    a "location" column plus a "date" column and one column per hourly
    variable requested.
    """
    latitude, longitude = get_location_coordinates(location_name, mapping_df, mapping_path)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": HOURLY_VARIABLES,
        "timezone": "Asia/Bangkok",
        "past_days": past_days,
    }
    if forecast_days is not None:
        params["forecast_days"] = forecast_days

    responses = openmeteo.weather_api(OPEN_METEO_URL, params=params)
    response = responses[0]
    hourly = response.Hourly()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        ).tz_convert(response.Timezone().decode())
    }
    for i, name in enumerate(HOURLY_VARIABLES):
        hourly_data[name] = hourly.Variables(i).ValuesAsNumpy()

    df = pd.DataFrame(hourly_data)
    df.insert(0, "location", location_name)
    return df


if __name__ == "__main__":
    mapping = load_location_mapping()
    sample_location = mapping.iloc[0]["commune_name"]
    hourly_dataframe = fetch_meteo_data(sample_location)
    print(f"Fetched {len(hourly_dataframe)} hourly rows for '{sample_location}'")
    print(hourly_dataframe.head())
