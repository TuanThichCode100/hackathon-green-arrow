from pathlib import Path
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipelines.inference import build_output  # noqa: E402

app = FastAPI(title="Green Arrow API", version="0.1.0")


class ForecastRequest(BaseModel):
    location_name: str
    horizon_name: str = "day3"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/forecast")
def forecast(payload: ForecastRequest) -> dict:
    try:
        mapping_path = ROOT / "data" / "maping_location.csv"
        if not mapping_path.exists():
            raise FileNotFoundError(f"Location mapping file not found: {mapping_path}")

        mapping_df = pd.read_csv(mapping_path)
        if "commune_name" not in mapping_df.columns:
            raise ValueError(f"Location mapping file is missing 'commune_name': {mapping_path}")

        normalized = payload.location_name.strip().casefold()
        match = mapping_df[mapping_df["commune_name"].astype(str).str.strip().str.casefold() == normalized]
        if match.empty:
            available = ", ".join(map(str, mapping_df["commune_name"].astype(str).head(10).tolist()))
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Location '{payload.location_name}' was not found in {mapping_path}. "
                    f"Use a value from the commune_name column. Sample values: {available}"
                ),
            )

        return build_output(payload.location_name, payload.horizon_name)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
