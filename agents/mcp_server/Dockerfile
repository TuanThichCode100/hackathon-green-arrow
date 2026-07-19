# Sử dụng image Python gọn nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements.txt và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào thư mục làm việc
COPY . .

# Mở cổng 8000 cho MCP server
EXPOSE 8000

# Thiết lập biến môi trường mặc định (Có thể ghi đè lúc run)
ENV PORT=8000

# Command để chạy MCP server
CMD ["python", "main.py"]
