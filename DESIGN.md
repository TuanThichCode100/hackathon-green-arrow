# GreenForecast Design System

## Overview

Giao diện sản phẩm sáng, tiết chế và tập trung vào bản đồ hành chính Điện Biên. Không gian làm việc mô phỏng một bàn tác nghiệp vào ban ngày: nền giấy hơi xanh, chữ than đậm, đường phân cách mảnh và một màu nhấn xanh lá dùng cho hành động chính.

## Color Palette

- `--canvas`: `oklch(0.974 0.006 155)`
- `--surface`: `oklch(0.992 0.004 155)`
- `--surface-muted`: `oklch(0.948 0.009 155)`
- `--ink`: `oklch(0.235 0.022 160)`
- `--ink-muted`: `oklch(0.48 0.018 160)`
- `--line`: `oklch(0.885 0.012 155)`
- `--accent`: `oklch(0.52 0.13 154)`
- `--accent-strong`: `oklch(0.42 0.12 154)`
- `--safe`: `oklch(0.58 0.12 154)`
- `--watch`: `oklch(0.72 0.13 78)`
- `--danger`: `oklch(0.56 0.18 28)`
- `--info`: `oklch(0.58 0.12 230)`

Không dùng đen hoặc trắng tuyệt đối. Màu nguy cơ chỉ dành cho dữ liệu và trạng thái, không dùng trang trí.

## Typography

- Font duy nhất: Geist Sans qua `next/font/google`.
- Số liệu: Geist Mono qua `next/font/google`.
- Heading không dùng serif.
- Scale: 12, 13, 14, 16, 20, 24, 32 px.
- Body line-height 1.5; nhãn compact 1.25.

## Layout

- App shell gồm navigation rail 236 px, header 72 px và vùng nội dung linh hoạt.
- Desktop ưu tiên khung bản đồ lớn với panel điều hành bên phải.
- Tablet thu gọn navigation thành icon rail.
- Mobile chuyển thành top navigation và một cột duy nhất.
- Khoảng cách theo nhịp 4, 8, 12, 16, 24, 32 px.

## Surfaces

- Bán kính nhỏ và có mục đích: 10 px cho control, 14 px cho panel.
- Không lồng card trong card.
- Shadow chỉ dùng cho slide-over, popover và lớp nổi.
- Phân nhóm bằng khoảng trắng, nền nhẹ và đường phân cách 1 px.

## Controls

- Icon duy nhất từ `@phosphor-icons/react`, weight `regular` hoặc `bold` cho trạng thái chọn.
- Button cao 40 px, primary dùng accent, secondary dùng surface và border.
- Hover thay đổi nền; active dịch chuyển `translateY(1px)`.
- Focus ring 2 px, tương phản rõ.
- Form luôn có label phía trên và lỗi phía dưới.

## Map

- Không dùng basemap tile ngoài tỉnh.
- Nền ngoài ranh giới tỉnh được loại bỏ hoàn toàn.
- Ranh giới tỉnh có stroke đậm; từng xã là polygon có stroke 1 px.
- Fill theo trạng thái safe, watch, danger; selected tăng stroke và độ sáng.
- Hover hiển thị tên xã, loại rủi ro và tỷ lệ tiếp cận.
- Legend luôn có cả màu, nhãn và mô tả.

## Motion

- 160–220 ms, `cubic-bezier(0.16, 1, 0.3, 1)`.
- Chỉ animate opacity và transform.
- Không có motion trang trí hoặc vòng lặp vô hạn.
- Skeleton shimmer được tắt khi người dùng chọn reduced motion.

## States

- Loading dùng skeleton theo đúng cấu trúc màn hình.
- Empty state giải thích dữ liệu nào còn thiếu và hành động tiếp theo.
- Error state nằm tại nơi lỗi xảy ra, có nút thử lại.
- Dữ liệu mô phỏng có nhãn “Mô phỏng”.
