# Prediction Service

Module này cô lập mã và tài sản dự báo thời tiết/thiên tai khỏi backend vận hành và frontend.

## Interface hiện tại

- `GET /health` trả trạng thái sẵn sàng của service.
- `POST /forecast` nhận `location_name` và `horizon_name` (`day3` hoặc `day7`), trả hợp đồng dự báo do `src/pipelines` tạo ra.

Chạy cục bộ từ thư mục này:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8001
```

Dockerfile cũng được đặt tại đây và phải build với `ml-service/` là build context:

```powershell
docker build -t greenforecast-ml ./ml-service
```

`docker-compose.yml` ở root **chưa** khởi chạy Prediction Service. Backend hiện không gọi trực tiếp service này; việc tích hợp là một đầu việc riêng để tránh công bố dự báo thử nghiệm như dữ liệu vận hành.

## Cấu trúc

- `src/pipelines/`: pipeline dự báo hiện tại.
- `models/`: artifact mô hình mà pipeline hiện tại đọc.
- `data/`: dữ liệu phục vụ ML, gồm bảng ánh xạ địa danh cho Open-Meteo.
- `scripts/legacy/`: script tải và gộp dữ liệu lịch sử theo đường dẫn cũ; cần chuẩn hóa trước khi dùng lại.
- `notebooks/`: notebook nghiên cứu.
- `legacy/`: prototype ML cũ, không có caller và không phải service được hỗ trợ.

Nguồn địa giới hành chính năm 2025 vẫn ở `../data/`, bởi đó là dữ liệu của bản đồ frontend chứ không phải dữ liệu của module này.
