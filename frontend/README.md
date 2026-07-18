# GreenForecast — CRM Cảnh báo Thời tiết (Next.js)

Dashboard CRM cho **cán bộ tỉnh/xã** giám sát và phân phối cảnh báo thời tiết cực đoan
(hệ thống DBWAS — tỉnh Điện Biên). Được chuyển từ prototype HTML sang **Next.js 14 (App Router)**.

## Chạy dự án

```bash
cd greenforecast-nextjs
npm install
npm run dev        # http://localhost:3000
```

Build production:

```bash
npm run build && npm start
```

Yêu cầu: Node.js 18.17+ .

## Cấu trúc

```
greenforecast-nextjs/
├─ app/
│  ├─ layout.jsx        # <html>, font, metadata, import globals.css
│  ├─ page.jsx          # render <Dashboard/>
│  └─ globals.css       # reset, font Be Vietnam Pro, keyframes, hover
├─ components/
│  └─ Dashboard.jsx     # 'use client' — toàn bộ UI + state + bản đồ Leaflet
├─ lib/
│  ├─ data.js           # dữ liệu mock + buildModel()/buildDetail() (thuần JS)
│  └─ style.js          # s(): chuỗi CSS -> style object của React
├─ package.json
├─ next.config.mjs
└─ jsconfig.json        # alias "@/*"
```

## Màn hình (6 view, đổi qua sidebar)

- **Bản đồ giám sát** — bản đồ Leaflet (CartoDB tiles), marker theo trạng thái xã, vòng ranh giới đỏ nhạt, pinpoint đỏ nhấp nháy cho người chưa phản hồi; click marker/thẻ xã mở panel chi tiết.
- **Tổng quan** — KPI, tỷ lệ phân phối theo kênh, phân bố dân tộc, hoạt động gần đây.
- **Danh sách Xã** — bảng thống kê quân số, click mở chi tiết.
- **Văn bản chỉ đạo (RAG)** — danh sách + trạng thái hiệu lực + modal upload.
- **Thống kê** — thẻ kênh (Zalo/SMS/Auto-call/Loa) + nhật ký gửi tin.
- **Phân quyền** — mô tả quyền theo cấp, đồng bộ với vai trò đang đăng nhập.

Điều khiển toàn cục ở topbar/sidebar: **bộ lọc thời gian** (Hôm nay/24h/7 ngày/30 ngày),
**chuyển vai trò** (Tỉnh/Xã), **toggle Khẩn cấp/Bình thường** (đổi toàn bộ số liệu & bản đồ).

## State (trong `Dashboard.jsx`)

`view`, `role`, `timeRange`, `emergency`, `detailId`, `uploadOpen`, `toast/toastIcon`, `clock`.
Tất cả số liệu hiển thị được tính từ `buildModel(emergency, timeRange)` và
`buildDetail(id, emergency)` trong `lib/data.js`.

## Ghi chú kỹ thuật

- **Leaflet** được import động (`await import('leaflet')`) trong `useEffect` để chỉ chạy phía client; bản đồ được huỷ/khởi tạo lại khi đổi view hoặc toggle khẩn cấp.
- **Style**: prototype dùng inline-style dạng chuỗi; helper `s()` chuyển chuỗi đó thành object cho React, giữ nguyên độ chính xác. Có thể refactor dần sang CSS Modules/Tailwind nếu muốn.
- Font tiêu đề: **Georgia** (serif); UI: **Be Vietnam Pro**.

## Gắn API thật (thay dữ liệu mock)

`lib/data.js` là nơi duy nhất chứa dữ liệu. Map sang các endpoint trong PRD:

| Chức năng | Endpoint gợi ý |
| --- | --- |
| Marker + trạng thái xã | `GET /api/dashboard/map-data` |
| Chi tiết xã (thôn bản, log, tỷ lệ) | `GET /api/communes/{id}/detail` |
| Upload văn bản RAG | `POST /api/policy/upload` |

Đổi `buildModel`/`buildDetail` thành hàm async gọi API (hoặc dùng React Query/SWR),
giữ nguyên hình dạng object trả về là UI chạy không cần sửa.
Với NFR "hands-free realtime", thay polling bằng WebSocket/SSE cập nhật state.

## Nguồn

Chuyển từ prototype `CRM Can Bo DBWAS.dc.html`. Dữ liệu địa bàn/dân số là **mock minh hoạ**, không phải số liệu chính thức.
