"""Small example that uses the production Open-Meteo preprocessing pipeline."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.preprocessing.open_meteo import (  # noqa: E402
    fetch_open_meteo_forecast,
    write_preprocessed_data,
)


if __name__ == "__main__":
    model_features = fetch_open_meteo_forecast(
        latitude=21.386,
        longitude=103.023,
        forecast_days=7,
        timezone="Asia/Bangkok",
    )
    output = write_preprocessed_data(
        model_features, REPO_ROOT / "data" / "meteo_model_input.csv"
    )
    print(model_features.head())
    print(f"Saved {len(model_features)} rows to {output}")
