# Nhật ký cập nhật hệ thống GreenForecast (Green Arrow Hackathon)

Tài liệu này ghi lại toàn bộ các tính năng, module và kiến trúc hệ thống đã được phát triển, phân chia theo từng thư mục/thành phần chính của dự án.

# Backend
- **Công nghệ lõi**: Sử dụng FastAPI, SQLAlchemy (ORM) và Pydantic (Validation). Hỗ trợ cơ sở dữ liệu linh hoạt (SQLite cho môi trường local/dev và PostgreSQL cho production).
- **Xác thực và Phân quyền (Security & RBAC)**:
  - **Supabase Auth**: Triển khai luồng xác thực JWT bảo mật qua thư viện `gotrue`.
  - **Validation 2 lớp**: JWT được xác thực offline (kiểm tra chữ ký bằng `SECRET_KEY`) và online (xác thực với API của Supabase).
  - **Role-Based Access Control (RBAC)**: Tách biệt quyền thao tác rõ ràng giữa cấp "Tỉnh" (`tinh`) và cấp "Xã" (`xa`) bằng dependency `require_role`.
- **Quản lý Điều hành & Cảnh báo**:
  - Giao diện API mô phỏng việc kích hoạt cảnh báo khẩn cấp (`manual-trigger`). Mọi quyết định đều được ghi vào bảng `AgentDecision` và theo dõi quá trình thực thi.
  - Các cảnh báo đa kênh (SMS, Zalo, Call, Loa phát thanh) đều được tạo thành bản ghi `Notification` có thời gian và trạng thái (delivered, failed, pending).
  - Cung cấp endpoint thao tác nhanh "Gửi lại" (`/resend`) hoặc "Gọi tự động" (`/call`) cho trưởng bản.
- **Bảo mật Kho lưu trữ (AES-256 / RAG)**:
  - Xây dựng module nhận file PDF/DOC/TXT (chỉ thị, công điện) làm ngữ cảnh học tăng cường (RAG) cho LLM.
  - **Mã hóa mức Quân đội (AES-256)**: File được mã hóa byte array bằng thuật toán AES-256 (Fernet) trước khi đẩy lên bucket của Supabase Storage với định dạng `.enc`, ngăn chặn truy cập trái phép.
- **Thống kê & Bộ lọc thời gian (Analytics)**:
  - Xây dựng hàm `get_start_date` ở backend để lọc linh hoạt các dữ liệu Notification, tính toán lại tổng quan kênh phát sóng theo `time_range` (Hôm nay, 24 giờ, 7 ngày, 30 ngày).

# Frontend

## Quá trình phát triển

### Giai đoạn 1 — Khảo sát và tái cấu trúc frontend

- Phân tích giao diện cũ và luồng hoạt động trong file HTML prototype.
- Chuyển frontend thành ứng dụng **Next.js 16.2**, **React 19.2** và **TypeScript**.
- Tách dashboard nguyên khối thành các component theo nghiệp vụ, giảm phụ thuộc giữa layout, dữ liệu và hành vi.
- Sử dụng **SWR** làm lớp truy vấn, cache và tái xác thực dữ liệu frontend.
- Chuẩn hóa biến môi trường cho backend API và Supabase.

### Giai đoạn 2 — Xây dựng lại UX/UI

- Xây dựng app shell gồm navigation rail 236 px, header 72 px và vùng workspace linh hoạt.
- Thay thế giao diện cũ bằng phong cách sáng, tiết chế, phù hợp môi trường điều hành hành chính; không sử dụng Glassmorphism hoặc Dark Mode.
- Đồng nhất font giao diện bằng **Geist Sans** và số liệu bằng **Geist Mono**.
- Chuẩn hóa design token theo OKLCH cho canvas, surface, ink, line, accent và các trạng thái safe/watch/danger.
- Đồng bộ icon bằng `@phosphor-icons/react`.
- Chuẩn hóa button, form, status pill, table, tooltip, toast, modal và slide-over.
- Bổ sung responsive breakpoint cho desktop, tablet và mobile.
- Bổ sung focus state, ARIA label, text label cho trạng thái màu và hỗ trợ `prefers-reduced-motion`.

### Giai đoạn 3 — Tách các màn hình nghiệp vụ

- `Dashboard`: app shell, điều phối view, toast, modal, slide-over và chế độ khẩn cấp.
- `Sidebar`: điều hướng, trạng thái active, tài khoản và các view được bảo vệ.
- `Header`: tiêu đề theo view, bộ lọc thời gian, đồng hồ và trạng thái đồng bộ.
- `OverviewView`: KPI, thống kê kênh, phân bố dân tộc và nhật ký hoạt động.
- `CommunesView`: danh sách địa bàn, dân số, mức tiếp cận và trạng thái.
- `CommuneDetailSlideOver`: chi tiết xã/phường và thôn bản mà không rời màn hình hiện tại.
- `ChannelsView`: thống kê và nhật ký phân phối cảnh báo.
- `PolicyView` và `UploadModal`: danh sách, trạng thái hiệu lực và upload văn bản.
- `RolesView`: trình bày vai trò và quyền truy cập.
- `ResidentsDB`: quản lý dữ liệu dân cư.
- `Login`: luồng xác thực cán bộ và quay lại chế độ quan sát.

### Giai đoạn 4 — Thiết kế lại bản đồ

- Thay marker điểm bằng polygon phân vùng cho từng xã/phường.
- Loại bỏ basemap các khu vực xung quanh, chỉ giữ phạm vi Điện Biên để tránh mất tập trung.
- Bổ sung fill, ranh giới, hover, tooltip, zoom, focus toàn tỉnh, legend và selected state.
- Cập nhật từ lớp 88 đơn vị cũ sang **45 đơn vị hành chính mới**, gồm 42 xã và 3 phường, hiệu lực từ 01/07/2025.
- Hợp nhất polygon GADM 4.1 theo quan hệ sáp nhập trong Nghị quyết 1661/NQ-UBTVQH15.
- Đối chiếu đủ 45/45 tên với `data/maping_location.csv`.
- Lưu bảng ánh xạ mới–cũ tại `data/dien_bien_admin_2025_mapping.csv` và GeoJSON tại `frontend/public/dien-bien-communes.geojson`.

### Giai đoạn 5 — Kết nối dữ liệu và xác thực

- Kết nối các endpoint communes, documents, overview, channels, ethnics, activities, predictions và notifications qua `frontend/lib/api.ts`.
- Tích hợp Supabase Auth cho luồng đăng nhập bằng email hoặc số điện thoại quy ước.
- Lưu access token để gửi Authorization header khi gọi các API cần xác thực.
- Cập nhật logout để gọi `supabase.auth.signOut()` và xóa trạng thái client.
- Hiển thị navigation theo trạng thái đăng nhập và vai trò người dùng.

### Giai đoạn 6 — Hoàn thiện các công cụ quản trị

- `ResidentsDB` đã kết nối GET/POST/PUT/DELETE và import danh sách cư dân.
- Bổ sung validation họ tên, số điện thoại, dân tộc và khả năng đọc SMS.
- CSV parser hỗ trợ dữ liệu có dấu phẩy và dấu nháy kép.
- Bổ sung pagination và bộ lọc theo xã, dân tộc.
- `UploadModal` đã kết nối `POST /api/documents/upload` bằng `FormData`, có validation, loading state và phản hồi lỗi/thành công.
- Bổ sung thao tác bật phiên khẩn cấp, gửi lại cảnh báo và gọi tự động từ màn hình chi tiết.

## Kiến trúc frontend hiện tại

- **Framework**: Next.js 16.2.10, React/React DOM 19.2.7.
- **Data fetching**: SWR 2.4.2.
- **Authentication**: Supabase JS và Supabase SSR.
- **Map**: Leaflet 1.9.4 và GeoJSON nội bộ.
- **Icon**: Phosphor Icons.
- **Typography**: Geist Sans và Geist Mono.
- **Styling**: CSS variables, CSS Grid/Flexbox và responsive media queries trong `frontend/app/globals.css`.

## Tài liệu frontend liên quan

- `DESIGN.md`: design system và quy tắc giao diện.
- `PRODUCT.md`: mục tiêu sản phẩm và nguyên tắc trải nghiệm.
- `app_workflow_v2.html`: luồng màn hình và hoạt động của web.
- `frontend/components/dashboard/`: các view và component dashboard.
- `frontend/lib/api.ts`: lớp kết nối API và chuyển đổi dữ liệu cho UI.
- `frontend/app/globals.css`: design token, layout, responsive và motion.

# Agents
- **Tích hợp LLM**: Tích hợp Google Gemini (gemini-1.5-flash) để đóng vai trò trợ lý sinh văn bản tự nhiên.
- **AI Agent Service**: Xử lý logic nghiệp vụ - khi có thiên tai, AI Agent tự động kết hợp thông tin cấu trúc (dân số, tọa độ) và dữ liệu RAG (từ các văn bản chỉ đạo) để sinh ra bản tin nhắn SMS / kịch bản Voice chuẩn xác gửi đến vùng ảnh hưởng.

# Database
- **Thiết kế Đa tầng**: Sử dụng mô hình Relational DB cho dữ liệu cấu trúc (Tài khoản, Cư dân, Quyết định Agent, Thông báo) và Object Storage (Supabase) để lưu trữ tệp tin.
- **Phân tách Dữ liệu theo Role**:
  - Cấu trúc ràng buộc dữ liệu sao cho Cán bộ Xã chỉ được truy cập, CRUD cư dân và xem báo cáo trong phạm vi `commune_id` của mình. Cán bộ Tỉnh sử dụng Admin SDK để bao quát tổng thể.
- **Dữ liệu Dân cư Chi tiết**: Tối ưu schema lưu trữ thông tin nhân khẩu (Dân tộc, Trình độ học vấn, SĐT) để hệ thống tự động ra quyết định phân loại kênh thông báo (Vd: Gọi điện tiếng dân tộc thay vì gửi SMS text cho người không biết chữ).

## Giai đoạn 7 — Chuẩn hóa cấu hình kết nối Supabase

- Loại bỏ connection string Supabase cũ bị hardcode trong Docker Compose; backend nhận secret lúc chạy từ `backend/.env`, không đưa secret vào image hoặc Git.
- Bổ sung mẫu `backend/.env.example` cho PostgreSQL Session pooler (cổng 5432), Supabase URL, publishable key, service-role key và JWT secret.
- Chuẩn hóa các biến Supabase backend trong `Settings`, tách khỏi các biến `NEXT_PUBLIC_*` chỉ dành cho frontend.
- Giữ nguyên `backend/.env` cục bộ hiện hữu; connection string thật chỉ được bổ sung khi có credential từ Supabase Dashboard.

## Giai đoạn 8 — Khôi phục backend và quản trị schema

- Backend dùng Supabase Session pooler thực tế và đã khởi động ổn định, không còn restart loop khi cấu hình database hợp lệ.
- Bổ sung endpoint `GET /health` trả trạng thái `healthy` hoặc `degraded`, trạng thái database và quy ước schema có version.
- Khi trung tâm dữ liệu không sẵn sàng, dependency database trả HTTP 503 với mã `DATA_CENTER_UNAVAILABLE` thay vì để ứng dụng mất kết nối hoặc crash.
- Loại bỏ `Base.metadata.create_all()` và seed dữ liệu mô phỏng khỏi startup production.
- Thiết lập Alembic cùng revision khởi tạo `0001_initial_schema`; schema Supabase được quản lý bằng `alembic upgrade head`.
- Cập nhật client Supabase backend để ưu tiên `SUPABASE_SECRET_KEY`, tương thích `SUPABASE_SERVICE_ROLE_KEY` cũ và chỉ khởi tạo client đặc quyền tại request cần dùng.
- Xác thực token qua Supabase Auth thay vì hardcode project, API key hoặc JWT signing secret cũ trong source code.

## Giai đoạn 9 — Dữ liệu frontend trung thực và trạng thái mất kết nối

- Loại bỏ fallback `buildModel()` và các KPI/rủi ro mô phỏng khi API dashboard lỗi.
- Không còn suy diễn tỷ lệ tiếp cận bằng jitter hoặc giá trị mặc định; dữ liệu thiếu hiển thị `—` và trạng thái `Chưa xác thực`.
- Bổ sung trạng thái màu, nhãn và pill `Chưa xác thực` trong lớp chuyển đổi dữ liệu frontend.
- Khi không liên lạc được backend, ứng dụng vẫn giữ app shell và hiển thị banner `Mất kết nối tới trung tâm dữ liệu` cùng thao tác thử kết nối lại.
- Kiểm tra Open-Meteo từ container backend thành công; client có timeout, kiểm tra HTTP status và scheduler chỉ ghi dự báo khi database sẵn sàng.

## Giai đoạn 10 — Tương tác bản đồ và tra cứu địa bàn

- Map dùng trạng thái rủi ro từ dữ liệu backend; không còn gán màu hoặc tỷ lệ bằng quy luật mô phỏng theo ID.
- Thêm trạng thái polygon, tooltip và chú giải `Chưa xác thực` cho các địa bàn chưa có dữ liệu vận hành.
- Một lần chọn polygon hoặc dòng danh sách chỉ chọn/focus địa bàn; slide-over chỉ mở qua nút `Xem chi tiết` rõ ràng.
- Smart focus chỉ bay camera khi địa bàn nằm ngoài khung nhìn, thời lượng 250 ms; giảm minZoom để bản đồ toàn tỉnh không bị cắt trên desktop.
- Hiển thị đủ địa bàn từ GeoJSON, bổ sung tìm kiếm keyword không dấu, fallback sai nhẹ tối đa hai ký tự, filter theo trạng thái và tự cuộn danh sách tới polygon được chọn.
- Ổn định lifecycle Leaflet khi SWR tái xác thực dữ liệu: không tái tạo map hoặc làm reset khung nhìn trong lúc người dùng chọn địa bàn; đồng thời làm sạch registry layer trước mỗi lượt khởi tạo.
- Bổ sung trạng thái rỗng `Không tìm thấy địa bàn phù hợp.` cho tổ hợp tìm kiếm/lọc không có kết quả.
- Sửa thao tác cuộn khi chọn xã: chỉ cuộn vùng danh sách nội bộ, không còn kéo cả trang làm bản đồ ra khỏi viewport; focus giữ nguyên mức zoom và chỉ bay tới tâm địa bàn khi tâm nằm ngoài khung nhìn.

## Giai đoạn 11 — Điều hướng mobile

- Chuyển navigation mobile thành bottom navigation cố định, cao 68 px, theo cấu trúc quen thuộc của ứng dụng di động: icon và nhãn ngắn, vùng chạm rõ ràng, có trạng thái mục đang chọn.
- Giữ 5 tác vụ chính trên taskbar: Bản đồ, Tổng quan, Địa bàn, Phân phối và Văn bản; các màn quản trị không làm quá tải điều hướng hiện trường.
- Đưa nhận diện GreenForecast lên đầu màn hình riêng với logo và tên ứng dụng; header nội dung nằm bên dưới, không còn trộn với thanh điều hướng.
- Dành khoảng đệm phía cuối app shell để nội dung không bị taskbar che khuất; duy trì `prefers-reduced-motion` và focus state hiện có.
- Kiểm thử Playwright ở viewport 390 × 844: bottom navigation hiển thị đúng đáy màn hình và chuyển sang Tổng quan thành công.

## Giai đoạn 12 — Rà soát và bàn giao kỹ thuật

- Sửa phép tổng hợp dashboard khi Supabase chưa có dữ liệu: không còn phát sinh `NaN`; các KPI phụ thuộc dân số và trưởng bản hiển thị `—` cùng nhãn `chưa có số liệu xác thực` khi không có bản ghi nguồn.
- Chuẩn hóa hàm định dạng số để giá trị không hợp lệ luôn hiển thị `—`, không lan truyền số giả vào UI.
- Xác nhận runtime: `GET /health` là `healthy`, database `available`, và Alembic ở revision `0001_initial_schema (head)`.
- Xác nhận build production Next.js và Docker image frontend thành công; frontend/backend container cùng đang chạy.
- Luồng map, tìm kiếm, chọn xã, trạng thái rỗng, bottom navigation và Tổng quan dữ liệu trống đã được kiểm thử bằng Playwright.
- Giới hạn bàn giao: phát SMS/Zalo/loa và phát tin AI chưa được kết nối với nhà cung cấp thực. Backend hiện có mã tạo trạng thái gửi hoặc nội dung dự phòng, nên không được xem là bằng chứng thông báo đã được phát ra ngoài hệ thống.

## Giai đoạn 13 — Dọn module prototype frontend

- Rút gọn `frontend/lib/data.ts` thành interface helper nhỏ phục vụ runtime (`fmt`, trạng thái, màu tỷ lệ, pill và khoảng thời gian); loại bỏ toàn bộ dữ liệu xã mô phỏng và các hàm `buildModel`/`buildDetail` không còn được gọi.
- Xóa `frontend/components/dashboard/Shared.tsx` và `frontend/lib/style.ts`, là cụm UI prototype không có import từ runtime tree.
- Cập nhật `frontend/README.md` theo kiến trúc Next.js hiện tại, endpoint backend thực và quy ước không dùng dữ liệu mô phỏng.

## Giai đoạn 14 — Chuẩn hóa Supabase frontend

- Xóa Supabase client cũ tại `frontend/lib/supabase.ts`, vốn không có caller và giữ fallback credential trong source.
- Xóa `frontend/test_supabase.js`, script chẩn đoán không được khai báo trong package workflow.
- Giữ `frontend/utils/supabase/clients.ts` là adapter Supabase phía trình duyệt duy nhất mà `app/page.tsx` và `Login.tsx` sử dụng.
## Giai đoạn 15 — Cô lập Prediction Service

- Tách toàn bộ mã, model, dữ liệu và Dockerfile dự báo ML khỏi root vào `ml-service/`; backend và frontend vận hành không thay đổi, Docker Compose vẫn chỉ khởi chạy hai dịch vụ đó.
- Chuẩn hóa ranh giới: `ml-service/app.py` cung cấp `GET /health` và `POST /forecast`; `ml-service/README.md` ghi rõ đây là service độc lập, chưa được tích hợp để tránh hiển thị dự báo thử nghiệm như dữ liệu vận hành.
- Tách pipeline ML cũ vào `ml-service/legacy/`, kèm README nêu rõ không có caller hiện tại và các đầu việc bắt buộc trước khi tái sử dụng.
- Giữ `data/build_dien_bien_admin_2025.py` và `data/dien_bien_admin_2025_mapping.csv` tại root, kèm `data/README.md`, vì chúng là nguồn địa giới cho bản đồ Điện Biên thay vì dữ liệu ML.
- Thêm `CONTEXT.md` để cố định thuật ngữ Prediction Service, Operational Backend, Administrative Geography Source và Legacy ML Prototype; cập nhật các tài liệu ML liên quan theo đường dẫn mới.
