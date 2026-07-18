# Project Status: Greenforecast CRM (hackathon-green-arrow)

1. **Dự án này là gì?**
Hệ thống CRM giám sát & cảnh báo thời tiết cực đoan cho cán bộ tỉnh Điện Biên (DBWAS). Sử dụng AI Agent để tự động sinh bản tin, gửi đa kênh (Zalo, SMS, Auto-Call, Audio Loa), phân loại theo dân tộc/ngôn ngữ.

6. **Mục tiêu hiện tại là gì?**
Tiếp tục triển khai Vector RAG (pgvector) trên Supabase Cloud và ghép file âm thanh TTS thực tế.

3. **Hệ thống đã hoàn thành những gì?**
- Đã Refactor Frontend từ JavaScript sang TypeScript, tái cấu trúc Dashboard monolith 48KB thành nhiều sub-components nhỏ trong `components/dashboard/`. Fix lỗi Build Type và Upgrade Next.js 16 + React 19 mới nhất.
- Đã xử lý triệt để lỗi giật/nháy liên tục của Leaflet Map và lỗi _leaflet_pos do React re-render gọi API.
- Frontend Next.js hoàn chỉnh giao diện CRM: Bản đồ Leaflet, Dashboard KPI, Danh sách xã, Thống kê kênh, Văn bản RAG, Phân quyền. Đã có Login Guard và Quản lý Dân cư.
- Đã Dockerize Frontend và Backend. Chuyển đổi Database sang Supabase Cloud PostgreSQL.
- Đã thiết kế kiến trúc Backend 9 Modules (Modular Monolith) với FastAPI.
- Đã Brainstorm thiết kế cấu trúc Database lõi PostgreSQL + PostGIS và Vector RAG (pgvector).
- Đã triển khai hoàn thiện Backend Module AI Agent tích hợp Gemini 1.5 Flash (Sinh bản tin khẩn cấp từ Open-Meteo và RAG Document) với luồng Human-in-the-loop (Cán bộ duyệt) an toàn tuyệt đối.

4. **Đang làm gì?**
- Tích hợp kết nối Frontend gọi trực tiếp API sinh bản tin (Draft) từ Agent Module.

5. **Chưa làm gì?**
- Triển khai Vector Search thực tế trên pgvector Supabase Cloud.
- Ghép file âm thanh (TTS Templates) thực tế.

6. **Những Block lớn là gì?**
- Database: Không còn block. Đã migrate thành công lên Supabase Cloud, có sẵn pgvector.

7. **Việc ưu tiên tiếp theo?**
- Triển khai Module AI Agent tích hợp LLM.
