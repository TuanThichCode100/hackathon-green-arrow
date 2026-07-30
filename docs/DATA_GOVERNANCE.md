# Chính sách dữ liệu cho văn bản chỉ đạo

## Phạm vi

Tài liệu này áp dụng cho tệp văn bản chỉ đạo được tiếp nhận, xử lý OCR/SLM,
xác nhận, xem bản gốc, xóa mềm và xóa vĩnh viễn trong GreenForecast.

## Lưu trữ và mã hóa

- Bản gốc được mã hóa ở backend trước khi đưa vào Supabase Storage private bucket.
- Khóa mã hóa chỉ tồn tại ở backend. API và frontend không trả về khóa, object key
  công khai hoặc URL tải xuống dài hạn.
- Database lưu hash SHA-256 để kiểm tra toàn vẹn, metadata và nội dung đã được cán
  bộ duyệt. Hash không được dùng thay cho mã hóa.

## Xử lý AI

- OCR dùng VietOCR CPU-first và có thể dùng CUDA khi hạ tầng có GPU; Google Vision
  chỉ là fallback cho kết quả chất lượng thấp.
- Cấu hình runtime cần `GOOGLE_VISION_API_KEY` cho fallback, cùng `LLM_BASE_URL`,
  `LLM_API_KEY` và `LLM_MODEL` cho endpoint OpenAI-compatible của 9router.
- Chỉ OCR text cần cho trích xuất được gửi qua 9router tới model SLM. Không gửi bản
  gốc; tắt retention/training ở nhà cung cấp khi cấu hình đó khả dụng.
- Kết quả AI là bản nháp, không tự đưa vào giao diện chính hoặc AI Agent.

## Vòng đời và quyền

- `processing`, `pending_review`, `failed` chỉ người upload xem được trong 24 giờ.
- `approved` mới hiển thị theo phạm vi địa bàn và được AI Agent tham chiếu.
- `deleted` được giữ 30 ngày trước khi xóa vĩnh viễn. Tất cả cán bộ thấy metadata,
  người xóa và cán bộ tỉnh xem chi tiết; chỉ cán bộ tỉnh khôi phục.
- Cán bộ xã muốn xem bản gốc phải gửi yêu cầu. Yêu cầu hết hạn sau 24 giờ; quyền
  được duyệt có hiệu lực 24 giờ. Cán bộ tỉnh xem ngay khi chính sách văn bản cho phép.

## Audit và thông báo

Mọi upload, sửa bản nháp, xác nhận, xóa, khôi phục và yêu cầu xem bản gốc phải tạo
audit event có người thực hiện, vai trò, thời điểm và chi tiết thay đổi tối thiểu.
Giao diện Thông báo chỉ hiển thị diễn giải đã phân quyền, không hiển thị OCR/JSON thô.
