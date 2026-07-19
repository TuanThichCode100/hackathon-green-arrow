# Hướng dẫn chạy Test MCP Client

Thư mục này chứa một đoạn mã Python `test_client.py` đóng vai trò như một Agent/Client kết nối tới MCP Server của bạn thông qua giao thức SSE. Nó sẽ thử:
1. Kết nối vào `http://localhost:8000/sse`.
2. Khởi tạo MCP session.
3. Fetch (liệt kê) danh sách tools đang có để kiểm tra kết nối.
4. Gọi tool `send_telegram_message` với một thông điệp mẫu để test xem Telegram có nhận được tin nhắn hay không.

## 🛠️ Yêu cầu trước khi test
1. Đảm bảo MCP Server đã được khởi chạy bằng Docker (`docker-compose up -d`) và cổng `8000` đang mở.
2. Bạn đã cấu hình thành công `.env` (chứa `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`) ở ngoài thư mục `mcp_server`.

## 🚀 Cách chạy
Mở terminal và di chuyển vào thư mục chứa thư mục `test` (hoặc đứng trực tiếp trong `test`):

```bash
# Cài đặt thư viện mcp (nếu máy host của bạn chưa có, đây là môi trường máy thật của bạn để chạy script client)
pip install mcp[cli] httpx-sse

# Chạy file test
python test_client.py
```

## 📝 Kết quả mong đợi (Expected Output)
```text
[*] Đang kết nối tới MCP server tại http://localhost:8000/sse...
[+] Đã kết nối và khởi tạo MCP Session thành công!

[*] Đang lấy danh sách các tools...
  -> Tool tìm thấy: 'send_telegram_message' | Mô tả: Gửi tin nhắn văn bản đến Telegram.

[*] Đang gọi tool 'send_telegram_message'...
[+] Kết quả trả về từ Server:
  -> Tin nhắn đã được gửi thành công đến Telegram.
```
Nếu bạn nhận được kết quả như trên và điện thoại ting ting có tin nhắn từ Bot, nghĩa là Server của bạn đã hoạt động hoàn hảo! 🎉
