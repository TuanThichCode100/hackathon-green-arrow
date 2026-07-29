# GreenForecast

GreenForecast là hệ thống hỗ trợ theo dõi rủi ro thiên tai và điều phối cảnh báo cho tỉnh Điện Biên.

## Module đang vận hành

- `frontend/`: ứng dụng Next.js cho cán bộ vận hành.
- `backend/`: Operational Backend FastAPI, kết nối Supabase và Open-Meteo.
- `data/`: nguồn địa giới hành chính Điện Biên năm 2025 cho bản đồ.

Khởi động hai dịch vụ vận hành:

```powershell
docker compose up --build
```

Frontend chạy tại `http://localhost:3000`; backend chạy tại `http://localhost:8000`.

## Dự báo ML

`ml-service/` là Prediction Service độc lập. Nó chưa được nối vào Docker Compose hoặc Operational Backend, do đó không được trình bày kết quả dự báo của nó như dữ liệu vận hành đã xác thực. Xem [hướng dẫn module](ml-service/README.md) để chạy và phát triển riêng.

## Tài liệu

- `UPDATES.md`: lịch sử thay đổi đã bàn giao.
- `CONTEXT.md`: thuật ngữ và ranh giới domain.
- `DESIGN.md` và `PRODUCT.md`: định hướng sản phẩm, UX/UI.
