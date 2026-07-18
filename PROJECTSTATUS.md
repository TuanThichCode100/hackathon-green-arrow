# Project Status: Greenforecast CRM (hackathon-green-arrow)

1. **Dự án này là gì?**
Hệ thống CRM giám sát & cảnh báo thời tiết cực đoan cho cán bộ tỉnh Điện Biên (DBWAS). Sử dụng AI Agent để tự động sinh bản tin, gửi đa kênh (Zalo, SMS, Auto-Call, Audio Loa), phân loại theo dân tộc/ngôn ngữ.

2. **Mục tiêu hiện tại là gì?**
Đối chiếu nghiệp vụ từ spec (Google Sheets) với frontend → thiết kế API schema → xây backend.

3. **Hệ thống đã hoàn thành những gì?**
- Frontend Next.js 14 hoàn chỉnh giao diện CRM: Bản đồ Leaflet, Dashboard KPI, Danh sách xã, Thống kê kênh, Văn bản RAG, Phân quyền
- 10 xã mock data, 4 kênh gửi tin, phân quyền 2 vai trò (Tỉnh/Xã)
- Chế độ khẩn cấp + API call tới backend (POST /api/trigger-alert)
- Đã phân tích đối chiếu 30 mục nghiệp vụ: 13 đạt, 9 đạt một phần, 8 thiếu (~43% đồng nhất)
- Đã thiết kế 30+ endpoint API chia 9 nhóm

4. **Đang làm gì?**
Chờ duyệt phân tích & API schema → quyết định bước triển khai tiếp theo.

5. **Chưa làm gì?**
- Backend (hoàn toàn trống)
- Models AI (hoàn toàn trống)
- Hiển thị dữ liệu thời tiết realtime trên frontend (thiếu hoàn toàn)
- Quản lý cư dân/danh bạ SĐT
- Mở rộng 115 xã thực tế
- 25+ loại thiên tai

6. **Những Block lớn là gì?**
- Frontend: Next.js 14 (đã có, cần bổ sung weather panel + resident management)
- Backend: Chưa khởi tạo (cần FastAPI/Django + PostgreSQL + Vector DB)
- Models: Chưa khởi tạo (AI Agent sinh bản tin + TTS tiếng dân tộc)
- External: Open-Meteo, OpenWeatherMap, Trạm KTTV, Zalo OA, SMS Gateway

7. **Việc ưu tiên tiếp theo?**
- Xây backend API framework (FastAPI recommended)
- Kết nối nguồn dữ liệu thời tiết (Open-Meteo miễn phí)
- Bổ sung weather widget trên frontend Dashboard
