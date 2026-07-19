@echo off
echo Dang khoi dong Model Microservice...
echo.
echo Model se chay tai dia chi: http://localhost:5050/predict
echo.
uvicorn model_server:app --host 0.0.0.0 --port 5050 --reload
