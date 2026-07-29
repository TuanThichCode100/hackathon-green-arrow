# Legacy ML prototype

Thư mục này lưu pipeline ML trước đây để tránh làm mất tư liệu, nhưng không nằm trên đường chạy của Docker Compose, backend hoặc frontend.

- `model_server.py` đang import package `pipeline` của prototype cũ và không còn là endpoint được hỗ trợ.
- `pipeline/`, `tests/` và `artifacts/` là mã, kiểm thử và model bundle của prototype đó.
- `notebooks/` là notebook nghiên cứu cũ.

## Việc cần làm trước khi tái sử dụng

1. Chọn duy nhất một pipeline thay vì duy trì song song với `../src/pipelines`.
2. Chuẩn hóa package/import và dependency lock cho pipeline được chọn.
3. Xác nhận dataset, đánh giá lại model và thiết kế contract API trước khi nối vào Operational Backend.
4. Chỉ sau các bước trên mới thêm service này vào Docker Compose.
