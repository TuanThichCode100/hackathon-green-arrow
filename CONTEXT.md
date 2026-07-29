# GreenForecast Context

## Glossary

- **Prediction Service**: Module độc lập tạo dữ liệu dự báo thời tiết và rủi ro thiên tai từ Open-Meteo cùng các mô hình đã huấn luyện. Đây không phải backend nghiệp vụ vận hành dashboard.
- **Operational Backend**: Dịch vụ FastAPI trong `backend/`, cung cấp API, xác thực và dữ liệu vận hành cho frontend.
- **Administrative Geography Source**: Tệp và công cụ ở `data/` gốc dùng để duy trì ánh xạ đơn vị hành chính Điện Biên năm 2025 và GeoJSON bản đồ; không thuộc Prediction Service.
- **Legacy ML Prototype**: Pipeline ML cũ không nằm trên đường chạy của hệ thống hiện tại và được giữ lại chỉ để tham chiếu hoặc chuyển đổi có kiểm soát.
