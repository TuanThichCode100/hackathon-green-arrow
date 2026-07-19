@echo off
setlocal
chcp 65001 >nul

set "MODEL_PATH=%~dp0artifacts\disaster_model.joblib"

if "%~1"=="" (
    echo [LOI] Thieu toa do!
    echo Cach dung: predict_live.bat [vi_do] [kinh_do] [output_file]
    echo Vi du ^(Ha Noi^): predict_live.bat 21.0285 105.8542 predictions_hanoi.json
    exit /b 1
)

set "LAT=%~1"
set "LON=%~2"
set "OUTPUT=%~3"

if "%OUTPUT%"=="" (
    set "OUTPUT=predictions.json"
)

if not exist "%MODEL_PATH%" (
    echo [LOI] Khong tim thay mo hinh tai %MODEL_PATH%
    echo Vui long chay train_model.bat truoc.
    exit /b 1
)

echo Dang tai du lieu thoi tiet tu Open-Meteo va du bao cho toa do ^(%LAT%, %LON%^)...
python -m pipeline.inference.predict --model "%MODEL_PATH%" --latitude %LAT% --longitude %LON% --output "%OUTPUT%"
if "%errorlevel%"=="0" (
    echo Hoan tat! Ket qua duoc luu tai: %OUTPUT%
) else (
    echo [LOI] Qua trinh du bao that bai.
    exit /b %errorlevel%
)
