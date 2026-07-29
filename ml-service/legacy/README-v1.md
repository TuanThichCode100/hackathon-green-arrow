# Green Arrow — Natural Disaster Forecasting Pipeline

## Feature dataset mới

Training mặc định dùng contract động trong:

```text
weather_data/weather_merged_2021_2026_labeled_features.parquet
```

Chạy bằng một lệnh:

```bat
train_model.bat
```

Model sử dụng 136 feature thuộc allowlist dùng chung giữa Parquet và Open-Meteo;
các cột ngoài contract này được bỏ qua để tránh train một feature mà inference
không thể tái tạo. Artifact ghi lại chính xác danh sách feature đã train.
Inference Open-Meteo tải thêm 168 giờ quá khứ và tái tạo cùng lag/rolling
feature trước khi dự đoán.

Pipeline dự báo xác suất 5 loại thiên tai từ dữ liệu khí tượng:

- `y_mua_lon` — Mưa lớn
- `y_sat_lo` — Sạt lở
- `y_dong_loc` — Dông lốc
- `y_mua_da` — Mưa đá
- `y_lu_lut` — Lũ lụt

Ba pipeline dùng chung contract 136 feature từ Parquet:

```text
CSV/Parquet đã gán nhãn -> training -> disaster_model.joblib
Open-Meteo API + 168 giờ lịch sử -> preprocessing -> 136 model features
136 model features + model artifact      -> 5 xác suất / giờ dự báo
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

Hoặc trên Windows, chạy toàn bộ training bằng một lệnh:

```bat
train_model.bat "C:\path\weather_merged_2021_2026_labeled.csv" artifacts
```

Có thể thay đổi cấu hình BAT bằng environment variable:
`FORECAST_HORIZON_HOURS`, `CALIBRATION_FRACTION`, `VALIDATION_FRACTION`,
`MAX_ITERATIONS`, `MAX_ALERT_RATE`, `MIN_RECALL`, `MIN_PR_LIFT`,
`BACKTEST_FOLDS` và `BACKTEST_MAX_ITERATIONS`. Đặt `BACKTEST_FOLDS=2` hoặc lớn
hơn để chạy expanding-window temporal backtest; fold một class được đánh dấu
`available=false` thay vì trộn dữ liệu gây leakage. Chỉ với smoke test/data nhỏ,
có thể đặt
`ALLOW_UNCALIBRATED=1`; không nên dùng cho model production.

Pipeline sẽ:

1. kiểm tra schema/kiểu dữ liệu và loại các biến hằng/trùng đã chỉ ra trong
   notebook (`snow_depth`, `snowfall`, `rain`);
2. gộp các dòng trùng `location_id + time` giống logic trong notebook (mean cho
   thời tiết, max/OR cho nhãn);
3. dịch target tới horizon tương lai (mặc định `t + 24h`);
4. chia train/calibration/validation theo thời gian để không dùng tương lai dự
   báo quá khứ;
5. huấn luyện một `XGBClassifier` cho mỗi nhãn với histogram trees,
   `scale_pos_weight`, subsampling và early stopping;
6. hiệu chỉnh xác suất bằng Platt scaling, chọn threshold từ precision–recall
   curve theo recall tối thiểu/ngân sách cảnh báo và báo metric trên validation;
7. hiển thị `tqdm` cho 15 phase: train, calibrate và validate của 5 nhãn;
8. lưu mọi lần chạy; chỉ promote khi mọi target calibrated, PR-lift đạt chuẩn,
   recall dương, alert rate trong ngân sách và Brier skill dương:

```text
artifacts/
├── disaster_model.joblib       # best của experiment được promote gần nhất
├── metrics.json                # metrics + experiment_key tương ứng
├── best.json                   # manifest atomic, nguồn sự thật của active best
├── experiments/
│   └── <experiment_key>/
│       ├── disaster_model.joblib  # best trong cùng dataset/protocol
│       └── metrics.json
└── runs/
    └── 20260719T...Z/
        ├── disaster_model.joblib
        └── metrics.json
```

`experiment_key` được tạo từ fingerprint của dataset, horizon, time split và
feature contract. Các run khác experiment không bị so điểm với nhau. Một run
chỉ được promote khi validation có cả positive/negative và PR-AUC hợp lệ cho đủ
5 thiên tai. Việc promote dùng file lock; model/metrics của mỗi run là bất biến
và manifest `best.json` được atomic replace cuối cùng. Inference/evaluator sẽ
tự resolve manifest khi nhận `artifacts/disaster_model.joblib`, nên không thể
đọc nhầm model và metrics từ hai run khác nhau.

Thêm `--no-progress` nếu cần tắt progress bar trong CI/log file.

Output training có ba progress bar riêng và các dòng kết quả cố định:

```text
TRAIN:     100%|██████████| 5/5 [00:31<00:00, 6.20s/model]
[TRAIN 1/5] Mưa lớn (y_mua_lon) | time=6.42s | support=...

CALIBRATE: 100%|██████████| 5/5 [00:04<00:00, 1.18model/s]
[CALIBRATE 1/5] Mưa lớn (...) | time=0.91s | threshold=0.35 | calibrated=True

VALIDATE:  100%|██████████| 5/5 [00:07<00:00, 1.44s/model]
[VALIDATE 1/5] Mưa lớn (...) | time=1.41s | support=... |
prevalence=... | PR-AUC=... | PR-lift=... | ROC-AUC=... | Brier=... |
precision=... | recall=... | F1=... | threshold=... | calibrated=True
```

Nếu terminal không hỗ trợ Unicode, tên tiếng Việt tự chuyển sang dạng ASCII để
progress không bị lỗi encoding.

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

## Đánh giá model trên labeled holdout

Unit test kiểm tra pipeline có hoạt động đúng, nhưng không chứng minh model dự
báo tốt. Để chấm model, dùng một file labeled holdout độc lập, không được dùng
trong train/calibration/validation:

```powershell
python -m pipeline.evaluation.evaluate `
  --model artifacts/disaster_model.joblib `
  --data "C:\path\weather_holdout_labeled.csv" `
  --output artifacts/evaluation.json
```

Evaluator báo metric riêng cho từng thiên tai và summary toàn model:

- **PR-AUC / Average Precision — metric chọn best:** càng cao càng tốt. Với sự
  kiện hiếm, cần so với `prevalence`; ví dụ prevalence 0,1% thì random baseline
  chỉ khoảng 0,001. Không có một ngưỡng “tốt” áp dụng cho mọi bài toán.
- **Recall:** tỷ lệ thiên tai thật được phát hiện; quan trọng khi bỏ sót gây hậu
  quả lớn.
- **Precision:** trong các cảnh báo đã phát, bao nhiêu cảnh báo là đúng; thấp sẽ
  gây quá nhiều cảnh báo giả.
- **F1:** cân bằng precision và recall tại threshold đã chọn.
- **Brier score:** đánh giá xác suất; càng gần 0 càng tốt. Nên so với baseline
  luôn dự báo bằng prevalence.
- **ROC-AUC:** dùng tham khảo, nhưng có thể trông quá tốt trên dữ liệu cực mất
  cân bằng nên không dùng làm tiêu chí chọn best.

`artifacts/metrics.json` là kết quả validation dùng để chọn model trong quá
trình phát triển. `artifacts/evaluation.json` mới là kết quả đánh giá cuối nếu
file đầu vào thực sự là holdout chưa từng được model nhìn thấy.

## 3. Model Microservice (Dự báo Realtime qua Cổng 5050)

Để phục vụ cho Backend Team dễ dàng tích hợp dự báo thiên tai theo thời gian thực, hệ thống cung cấp một Microservice API độc lập, luôn mở tại **Cổng 5050**.

### Kiến trúc & Quy trình hoạt động (Data Flow)
1. **Lắng nghe Request:** Backend gửi một request (GET hoặc POST) chứa tọa độ địa lý (`lat`, `lon`) tới API.
2. **Kéo dữ liệu Realtime:** Dựa vào tọa độ đó, Microservice tự động call API của Open-Meteo để kéo về lịch sử thời tiết 168 giờ gần nhất (điều kiện bắt buộc để tính toán các tính năng mảng Lag/Rolling).
3. **Tiền xử lý (Preprocessing):** Toàn bộ dữ liệu thô được đẩy qua hàm tiền xử lý để tạo ra 146 tính năng (features) khớp chính xác với những gì Model đã được học.
4. **Suy luận (Inference):** Dữ liệu được đưa vào mô hình AI (`artifacts/disaster_model.joblib`) để dự báo.
5. **Trả về kết quả:** Trả về định dạng JSON đã được chuẩn hóa (tên thiên tai làm Key và giá trị là xác suất phần trăm) để Backend dễ dàng hiển thị lên UI.

### Hướng dẫn khởi chạy Microservice

**Cách 1: Chạy trực tiếp qua Script (Dành cho Development)**
Chỉ cần chạy file Batch đã được cung cấp sẵn:
```bat
start_server.bat
```
Server sẽ tự động lắng nghe tại `http://localhost:5050`. Bạn có thể truy cập `http://localhost:5050/docs` để xem giao diện Swagger UI và test API trực tiếp.

**Cách 2: Chạy qua Docker (Dành cho Deployment/Production)**
Toàn bộ Microservice đã được đóng gói chuẩn chỉnh bằng Docker để đảm bảo chạy mượt mà trên mọi môi trường (đặc biệt phù hợp khi nộp bài cho Ban giám khảo chấm thi).

Build Image:
```bash
docker build -t green-arrow-model .
```

Run Container:
```bash
docker run -d -p 5050:5050 --name ga_model green-arrow-model
```

### API Endpoint (`/predict`)

- **URL:** `http://localhost:5050/predict`
- **Method:** `POST` hoặc `GET`
- **Request Body (dành cho POST):**
  ```json
  {
    "lat": 21.0285,
    "lon": 105.8542,
    "target_time": "2026-07-20T12:00:00+07:00" 
  }
  ```
  *(Lưu ý: `target_time` là không bắt buộc. Nếu bỏ trống, API sẽ trả về toàn bộ dự báo 3 ngày tới).*

- **Response:**
  ```json
  {
    "prediction": {
      "forecast_time": "2026-07-20T12:00:00+07:00",
      "latitude": 21.0285,
      "longitude": 105.8542,
      "disasters": {
        "Mưa lớn": { "predicted": true, "probability_percent": 3.4414 },
        "Sạt lở": { "predicted": false, "probability_percent": 2.4898 },
        "Dông lốc": { "predicted": true, "probability_percent": 2.4483 },
        "Mưa đá": { "predicted": false, "probability_percent": 4.0360 },
        "Lũ lụt": { "predicted": false, "probability_percent": 1.3411 }
      }
    }
  }
  ```

## Giới hạn vận hành

Đây là xác suất đã được Platt-calibrate trên một lát cắt thời gian của dữ liệu
huấn luyện, không phải cảnh báo thiên tai chính thức. Trước khi phát cảnh báo
thực tế vẫn cần đánh giá calibration theo vùng/thời gian độc lập, giám sát data
drift, và kết hợp dữ liệu địa hình, thuỷ văn cùng nguồn cảnh báo của cơ quan
chức năng.

Pipeline dùng feature khí tượng tại `t` để dự báo nhãn tại `t + horizon`.
Lag/rolling được tạo riêng theo từng địa điểm từ tối đa 168 giờ quá khứ và không
sử dụng dữ liệu tương lai.
