@echo off
setlocal
chcp 65001 >nul

if "%~1"=="" (
  set "DATA_PATH=C:\Users\tranq\Downloads\weather_merged_2021_2026_labeled.csv"
) else (
  set "DATA_PATH=%~f1"
)

set "OUTPUT_DIR=%~2"
if "%OUTPUT_DIR%"=="" (
  set "OUTPUT_DIR=%~dp0artifacts"
) else (
  set "OUTPUT_DIR=%~f2"
)

if not defined FORECAST_HORIZON_HOURS set "FORECAST_HORIZON_HOURS=24"
if not defined CALIBRATION_FRACTION set "CALIBRATION_FRACTION=0.3"
if not defined VALIDATION_FRACTION set "VALIDATION_FRACTION=0.20"
if not defined MAX_ITERATIONS set "MAX_ITERATIONS=200"
if not defined LOKY_MAX_CPU_COUNT (
  if defined NUMBER_OF_PROCESSORS (
    set "LOKY_MAX_CPU_COUNT=%NUMBER_OF_PROCESSORS%"
  ) else (
    set "LOKY_MAX_CPU_COUNT=4"
  )
)
if not defined ALLOW_UNCALIBRATED set "ALLOW_UNCALIBRATED=1"
set "CALIBRATION_FLAG="
if /I "%ALLOW_UNCALIBRATED%"=="1" set "CALIBRATION_FLAG=--allow-uncalibrated"

pushd "%~dp0"
python -m pipeline.training.train ^
  --data "%DATA_PATH%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --forecast-horizon-hours %FORECAST_HORIZON_HOURS% ^
  --calibration-fraction %CALIBRATION_FRACTION% ^
  --validation-fraction %VALIDATION_FRACTION% ^
  --max-iterations %MAX_ITERATIONS% %CALIBRATION_FLAG%

set "TRAIN_EXIT_CODE=%errorlevel%"
popd
if not "%TRAIN_EXIT_CODE%"=="0" exit /b %TRAIN_EXIT_CODE%

echo.
echo Training completed.
if exist "%OUTPUT_DIR%\disaster_model.joblib" (
  echo Active best model: %OUTPUT_DIR%\disaster_model.joblib
  echo Active best metrics: %OUTPUT_DIR%\metrics.json
) else (
  echo This run was archived but was not eligible for best-model promotion.
)
