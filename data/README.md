# Dữ liệu địa giới và ánh xạ bản đồ

Thư mục này thuộc phần địa lý của ứng dụng, không thuộc `ml-service`.

- `build_dien_bien_admin_2025.py` tạo dữ liệu địa giới Điện Biên theo đơn vị hành chính hiệu lực từ 01/07/2025.
- `dien_bien_admin_2025_mapping.csv` ánh xạ tên đơn vị cũ sang đơn vị mới để tạo GeoJSON tại `frontend/public/dien-bien-communes.geojson`.

Khi cập nhật dữ liệu hành chính, phải kiểm tra nguồn chính phủ và cập nhật GeoJSON cùng bảng ánh xạ. Không di chuyển hai tệp này vào ML service vì chúng là nguồn cho trải nghiệm bản đồ.
