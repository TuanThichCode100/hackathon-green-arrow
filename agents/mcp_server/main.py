import os
import logging
import requests
from mcp.server.fastmcp import FastMCP

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramMCP")

# 1. Khởi tạo MCP server
mcp = FastMCP("TelegramAgent")

# 2. Định nghĩa tool để gửi tin nhắn Telegram
@mcp.tool()
def send_telegram_message(message: str, chat_id: str = "") -> str:
    """
    Gửi tin nhắn văn bản đến Telegram.
    
    Args:
        message: Nội dung văn bản cần gửi.
        chat_id: (Tuỳ chọn) ID của Telegram Chat hoặc Channel. 
                 Nếu không cung cấp, sẽ sử dụng biến môi trường TELEGRAM_CHAT_ID.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id if chat_id else os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token:
        return "Lỗi: Chưa thiết lập biến môi trường TELEGRAM_BOT_TOKEN."
    if not target_chat_id:
        return "Lỗi: Chưa thiết lập biến môi trường TELEGRAM_CHAT_ID và không có chat_id nào được cung cấp."
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message
    }
    
    try:
        logger.info(f"Đang gửi tin nhắn đến chat {target_chat_id}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return "Tin nhắn đã được gửi thành công đến Telegram."
    except requests.exceptions.RequestException as e:
        logger.error(f"Gửi tin nhắn thất bại: {e}")
        return f"Gửi tin nhắn thất bại: {str(e)}"

# 3. Chạy server ở chế độ SSE transport để luôn lắng nghe như một dịch vụ backend
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Đang khởi động Telegram MCP Server trên cổng {port} (SSE transport)...")
    uvicorn.run(mcp.sse_app, host="0.0.0.0", port=port)
