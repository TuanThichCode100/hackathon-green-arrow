# Green Arrow — Natural Disaster Forecasting Pipeline

Pipeline dự báo xác suất 5 loại thiên tai từ dữ liệu khí tượng:

- `y_mua_lon` — Mưa lớn
- `y_sat_lo` — Sạt lở
- `y_dong_loc` — Dông lốc
- `y_mua_da` — Mưa đá
- `y_lu_lut` — Lũ lụt

Ba pipeline dùng chung contract 12 feature đã phân tích trong
`notebooks/baseline.ipynb`:

```text
CSV/Parquet đã gán nhãn -> training -> disaster_model.joblib
Open-Meteo API          -> preprocessing -> 12 model features
12 model features + model artifact       -> 5 xác suất / giờ dự báo
```

## Cài đặt

Yêu cầu Python 3.10 trở lên:

```powershell
python -m pip install -r requirements.txt
```

## 1. Training pipeline

Input là CSV hoặc Parquet có `location_id`, `time`, 15 feature thời tiết nguồn
và 5 nhãn như trong notebook; model giữ lại 12 feature hữu ích:

```powershell
python -m pipeline.training.train `
  --data "C:\path\weather_merged_2021_2026_labeled.csv" `
  --output-dir artifacts `
  --forecast-horizon-hours 24 `
  --calibration-fraction 0.15 `
  --validation-fraction 0.2 `
  --max-iterations 200
```

Pipeline sẽ:

1. kiểm tra schema/kiểu dữ liệu và loại các biến hằng/trùng đã chỉ ra trong
   notebook (`snow_depth`, `snowfall`, `rain`);
2. gộp các dòng trùng `location_id + time` giống logic trong notebook (mean cho
   thời tiết, max/OR cho nhãn);
3. dịch target tới horizon tương lai (mặc định `t + 24h`);
4. chia train/calibration/validation theo thời gian để không dùng tương lai dự
   báo quá khứ;
5. huấn luyện một `HistGradientBoostingClassifier` có cân bằng lớp cho mỗi nhãn;
6. hiệu chỉnh xác suất bằng Platt scaling trên calibration set, chọn threshold
   trên calibration set và báo metric trên validation độc lập;
7. lưu:
   - `artifacts/disaster_model.joblib`
   - `artifacts/metrics.json`

Mặc định training sẽ dừng nếu bất kỳ nhãn nào không đủ hai class để calibration,
thay vì ghi raw score dưới tên xác suất. Với thử nghiệm kỹ thuật trên data nhỏ có
thể thêm `--allow-uncalibrated`; khi đó `probability_calibrated` trong
`metrics.json` và từng kết quả inference sẽ là `false` cho nhãn tương ứng.

## 2. Meteo preprocessing pipeline

Lấy forecast trực tiếp từ Open-Meteo và chuyển thành đúng 12 feature:

```powershell
python -m pipeline.preprocessing.open_meteo `
  --latitude 21.386 `
  --longitude 103.023 `
  --forecast-days 7 `
  --timezone Asia/Bangkok `
  --output data/meteo_model_input.csv
```

Open-Meteo trả các lớp đất chi tiết. Pipeline dùng trung bình hai điểm nhiệt độ
đất gần nhất và weighted average theo độ dày cho độ ẩm đất để tạo hai dải
`0–7 cm` và `7–28 cm` giống training schema. Request có retry/backoff và giới hạn
forecast từ 1 đến 16 ngày. Timestamp giữ timezone của response API.

Ví dụ Python tương đương nằm tại `notebooks/get_meteo_data.py`.

## 3. Inference pipeline

### Dự báo trực tiếp từ Open-Meteo

```powershell
python -m pipeline.inference.predict `
  --model artifacts/disaster_model.joblib `
  --latitude 21.386 `
  --longitude 103.023 `
  --forecast-days 7 `
  --timezone Asia/Bangkok `
  --output predictions.json
```

### Dự báo từ file đã preprocessing

```powershell
python -m pipeline.inference.predict `
  --model artifacts/disaster_model.joblib `
  --input data/meteo_model_input.csv `
  --output predictions.json
```

Mỗi giờ trong JSON output chứa vị trí, thời gian và kết quả của 5 thiên tai:

```json
{
  "feature_time": "2026-07-18T08:00:00+07:00",
  "forecast_time": "2026-07-19T08:00:00+07:00",
  "forecast_horizon_hours": 24,
  "latitude": 21.386,
  "longitude": 103.023,
  "hazards": [
    {
      "code": "y_mua_lon",
      "name": "Mưa lớn",
      "probability": 0.72,
      "probability_percent": 72.0,
      "probability_calibrated": true,
      "threshold": 0.45,
      "predicted": true
    }
  ]
}
```

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Test bao phủ contract Open-Meteo → model, artifact train/reload, và output
inference 5 nhãn.

## Giới hạn vận hành

Đây là xác suất đã được Platt-calibrate trên một lát cắt thời gian của dữ liệu
huấn luyện, không phải cảnh báo thiên tai chính thức. Trước khi phát cảnh báo
thực tế vẫn cần đánh giá calibration theo vùng/thời gian độc lập, giám sát data
drift, và kết hợp dữ liệu địa hình, thuỷ văn cùng nguồn cảnh báo của cơ quan
chức năng.

Baseline hiện dùng feature khí tượng tại `t` để dự báo nhãn tại `t + horizon`.
Lag/rolling theo từng địa điểm là bước mở rộng tiếp theo khi inference có nguồn
quan trắc lịch sử liên tục; không được tạo từ dữ liệu tương lai.
