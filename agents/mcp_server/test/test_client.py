import asyncio
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_test():
    # Đảm bảo bạn đã khởi chạy docker-compose hoặc main.py (SSE chạy ở cổng 8005)
    url = "http://localhost:8005/sse"
    print(f"[*] Đang kết nối tới MCP server tại {url}...")
    
    try:
        # Sử dụng sse_client để kết nối
        async with sse_client(url) as streams:
            # streams[0] là read_stream, streams[1] là write_stream
            async with ClientSession(streams[0], streams[1]) as session:
                
                # Khởi tạo MCP session (bắt buộc theo giao thức)
                await session.initialize()
                print("[+] Đã kết nối và khởi tạo MCP Session thành công!")
                
                # 1. Liệt kê các Tool mà server hỗ trợ
                print("\n[*] Đang lấy danh sách các tools...")
                response = await session.list_tools()
                
                tool_found = False
                for tool in response.tools:
                    print(f"  -> Tool tìm thấy: '{tool.name}' | Mô tả: {tool.description}")
                    if tool.name == "send_telegram_message":
                        tool_found = True
                        
                if not tool_found:
                    print("[-] Không tìm thấy tool 'send_telegram_message'. Hãy kiểm tra lại Server.")
                    return

                # 2. Thực thi (Call) Tool để gửi tin nhắn Telegram
                print("\n[*] Đang gọi tool 'send_telegram_message'...")
                test_message = "🚀 Đây là tin nhắn test từ MCP Client tự động (SSE Transport)!"
                
                try:
                    result = await session.call_tool(
                        "send_telegram_message",
                        arguments={"message": test_message}
                    )
                    
                    print("[+] Kết quả trả về từ Server:")
                    for content in result.content:
                        # Kết quả trả về trong result.content là một mảng TextContent
                        print(f"  -> {content.text}")
                        
                except Exception as e:
                    print(f"[-] Lỗi khi gọi tool (Kiểm tra lại Bot Token / Chat ID): {e}")
                    
    except ConnectionRefusedError:
        print("[-] Kết nối bị từ chối. Bạn đã chạy MCP Server (docker-compose up) chưa?")
    except Exception as e:
        print(f"[-] Lỗi kết nối: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
