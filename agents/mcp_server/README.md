# Telegram MCP Server

Đây là một service Model Context Protocol (MCP) hoạt động dưới dạng Backend Service (sử dụng SSE transport) để luôn lắng nghe trên cổng 8000. Service này cung cấp tool để hệ thống (agent) có thể gửi tin nhắn văn bản đến Telegram.

## Yêu cầu
- Docker và Docker Compose đã được cài đặt trên máy.

## Cài đặt và cấu hình

1. Copy file `.env.example` thành `.env`:
   ```bash
   cp .env.example .env
   ```

2. Cấu hình biến môi trường trong file `.env`:
   - `TELEGRAM_BOT_TOKEN`: Token của Telegram Bot (lấy từ [BotFather](https://t.me/botfather)).
   - `TELEGRAM_CHAT_ID`: ID của chat, group hoặc channel mặc định muốn nhận tin nhắn. Bạn có thể lấy ID bằng cách chat với con bot [@userinfobot](https://t.me/userinfobot).

## Cách chạy (Run)

Khởi động MCP server dưới dạng container luôn chạy (luôn lắng nghe):

```bash
docker-compose up -d --build
```

Service sẽ khởi động và lắng nghe trên cổng `8000`. Bạn có thể kiểm tra log bằng lệnh:
```bash
docker-compose logs -f
```

## Các Tools được cung cấp

Dịch vụ này expose tool sau thông qua giao thức MCP:

### 1. `send_telegram_message`
- **Mô tả:** Gửi một tin nhắn văn bản đến Telegram.
- **Tham số:**
  - `message` (string, bắt buộc): Nội dung tin nhắn bạn muốn gửi.
  - `chat_id` (string, không bắt buộc): ID của người nhận hoặc nhóm nhận. Nếu không điền, hệ thống sẽ sử dụng `TELEGRAM_CHAT_ID` đã khai báo trong file `.env`.

## Cách Agent tương tác với MCP server này

Agent sẽ kết nối với MCP server này qua giao thức HTTP Server-Sent Events (SSE) tại endpoint:
```
http://localhost:8000/sse
```
(Hoặc URL tương ứng nếu deploy trên server khác). Tùy thuộc vào Client MCP bạn đang sử dụng, bạn chỉ cần cấu hình transport dưới dạng SSE, trỏ tới URL này, hệ thống sẽ tự động list tools và có thể call tool thông qua HTTP request.
