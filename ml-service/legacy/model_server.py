from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from pathlib import Path

from pipeline.inference.predict import load_model, run_open_meteo_inference

# Global variable to hold our model
model_bundle = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_bundle
    model_path = Path("artifacts/disaster_model.joblib")
    if not model_path.exists():
        print(f"Warning: Model not found at {model_path}. You must run train_model.bat first.")
    else:
        print("Loading AI model into memory...")
        model_bundle = load_model(model_path)
        print("AI model loaded successfully!")
    yield
    # Clean up if necessary
    model_bundle = None

from pydantic import BaseModel

class PredictRequest(BaseModel):
    lat: float
    lon: float
    target_time: str | None = None

app = FastAPI(title="Disaster Prediction AI Microservice", lifespan=lifespan)

@app.post("/predict")
def predict_weather_post(request: PredictRequest):
    return _do_predict(request.lat, request.lon, request.target_time)

@app.get("/predict")
def predict_weather_get(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    target_time: str | None = Query(None, description="ISO 8601 target time")
):
    return _do_predict(lat, lon, target_time)

def _format_prediction(p: dict) -> dict:
    """Format the prediction to match the backend team's requested format."""
    formatted_hazards = {}
    for h in p["hazards"]:
        name = h["name"] # e.g. "Lũ lụt"
        formatted_hazards[name] = {
            "predicted": h["predicted"],
            "probability_percent": round(h["probability_percent"], 4)
        }
    
    return {
        "forecast_time": p["forecast_time"],
        "latitude": p["latitude"],
        "longitude": p["longitude"],
        "disasters": formatted_hazards
    }

def _do_predict(lat: float, lon: float, target_time: str | None):
    """
    Fetches Open-Meteo data for the coordinates, runs the AI model, and returns forecasts.
    """
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Train the model first.")

    try:
        # Run inference (fetches 168h history + forecast automatically)
        # We fetch 3 days of forecast to have a good coverage if target_time is in the future.
        predictions = run_open_meteo_inference(
            model_bundle,
            latitude=lat,
            longitude=lon,
            forecast_days=3,
            history_hours=168,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
        
    if not target_time:
        return {"predictions": [_format_prediction(p) for p in predictions]}
        
    # If a specific time is requested, filter the results
    try:
        target_dt = pd.Timestamp(target_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target_time format. Use ISO 8601.")
        
    for p in predictions:
        p_dt = pd.Timestamp(p["forecast_time"])
        if p_dt == target_dt:
            return {"prediction": _format_prediction(p)}
            
    raise HTTPException(status_code=404, detail=f"No forecast found for time: {target_time}. Forecast spans from {predictions[0]['forecast_time']} to {predictions[-1]['forecast_time']}")

if __name__ == "__main__":
    import uvicorn
    # Chạy ở port 5050 như yêu cầu của user
    uvicorn.run("model_server:app", host="0.0.0.0", port=5050, reload=True)
