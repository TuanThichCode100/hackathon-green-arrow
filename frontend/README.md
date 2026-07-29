# GreenForecast frontend

Giao diện Next.js cho hệ thống điều hành cảnh báo tỉnh Điện Biên.

## Chạy cục bộ

```bash
npm install
npm run dev
```

Ứng dụng chạy tại `http://localhost:3000`. Đặt `NEXT_PUBLIC_API_URL` trong `.env.local` khi backend không chạy tại `http://localhost:8000`.

## Runtime interface

- `app/page.tsx`: khởi tạo phiên Supabase và render dashboard.
- `components/Dashboard.tsx`: điều phối view, dữ liệu và trạng thái toàn cục của giao diện.
- `components/dashboard/`: map, tổng quan, địa bàn, phân phối, văn bản, phân quyền và các lớp tương tác.
- `lib/api.ts`: một interface duy nhất để chuyển đổi dữ liệu endpoint backend thành dữ liệu hiển thị.
- `lib/data.ts`: helper format, trạng thái và khoảng thời gian. File này không chứa dữ liệu mô phỏng.
- `utils/supabase/clients.ts`: adapter Supabase phía trình duyệt.

## Kiểm tra production

```bash
npm run build
```

Docker Compose ở root repository build và chạy frontend cùng backend:

```bash
docker compose up --build
```

## Dữ liệu và trạng thái

Frontend sử dụng dữ liệu thực từ backend. Khi dữ liệu vận hành chưa tồn tại hoặc backend không truy cập được, UI hiển thị `Chưa xác thực`, `—`, trạng thái rỗng hoặc banner mất kết nối; không dùng dữ liệu giả để thay thế.
