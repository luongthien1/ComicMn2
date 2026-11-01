# L1 – Phân tích chức năng hệ thống ComicMn2

## 1. Tổng quan hệ thống

ComicMn2 là phần mềm **quản lý truyện tranh** cho phép người dùng lưu trữ, tra cứu, cập nhật và xóa thông tin truyện tranh cùng danh sách chương của từng bộ truyện. Hệ thống gồm backend FastAPI + PostgreSQL và frontend React/TypeScript.

---

## 2. Các nhóm chức năng chính

### 2.1 Quản lý Truyện (Comic)

| ID | Chức năng | Mô tả |
|----|-----------|-------|
| F-CM-01 | Xem danh sách truyện | Hiển thị bảng truyện với tìm kiếm theo tên và lọc theo trạng thái |
| F-CM-02 | Xem chi tiết truyện | Xem thông tin đầy đủ (bìa, tác giả, thể loại, mô tả, trạng thái) kèm danh sách chương |
| F-CM-03 | Thêm truyện mới | Form nhập tên, tác giả, thể loại, mô tả, URL ảnh bìa, trạng thái |
| F-CM-04 | Sửa thông tin truyện | Cập nhật bất kỳ trường nào của truyện |
| F-CM-05 | Xóa truyện | Xóa truyện, tất cả chương bị xóa theo (cascade) |

### 2.2 Quản lý Chương (Chapter)

| ID | Chức năng | Mô tả |
|----|-----------|-------|
| F-CH-01 | Xem danh sách chương | Danh sách chương của một truyện, sắp xếp theo số thứ tự |
| F-CH-02 | Thêm chương | Nhập số chương (bắt buộc) và tên chương (tùy chọn) |
| F-CH-03 | Sửa chương | Cập nhật số và tên chương |
| F-CH-04 | Xóa chương | Xóa một chương khỏi truyện |

### 2.3 Tìm kiếm & Lọc

| ID | Chức năng | Mô tả |
|----|-----------|-------|
| F-SR-01 | Tìm theo tên | Tìm kiếm full-text không phân biệt hoa thường theo tên truyện |
| F-SR-02 | Lọc theo trạng thái | Lọc theo: Đang phát hành / Hoàn thành / Tạm dừng |

### 2.4 Giao diện

| ID | Chức năng | Mô tả |
|----|-----------|-------|
| F-UI-01 | Sidebar điều hướng | Menu dọc có thể thu gọn, highlight route active |
| F-UI-02 | Breadcrumb | Hiển thị vị trí hiện tại trong ứng dụng |
| F-UI-03 | Thông báo toàn cục | Alert success/error/warning/info xuất hiện góc trên phải |
| F-UI-04 | Modal form | Form tạo/sửa truyện và chương dạng modal overlay |
| F-UI-05 | Xác nhận xóa | Popconfirm xác nhận trước khi thực hiện xóa |

---

## 3. Trạng thái truyện

| Giá trị | Nhãn hiển thị | Màu tag |
|---------|--------------|---------|
| `ongoing` | Đang phát hành | Xanh dương |
| `completed` | Hoàn thành | Xanh lá |
| `paused` | Tạm dừng | Cam |

---

## 4. Actors

| Actor | Mô tả |
|-------|-------|
| Người dùng | Dùng trình duyệt để thao tác CRUD truyện và chương |
| FastAPI Backend | Xử lý business logic, lưu dữ liệu vào PostgreSQL |
| PostgreSQL | Lưu trữ dữ liệu truyện và chương |

---

## 5. Yêu cầu phi chức năng

| ID | Yêu cầu | Chi tiết |
|----|---------|---------|
| NFR-01 | API phản hồi nhanh | < 300ms cho CRUD thông thường |
| NFR-02 | Toàn vẹn dữ liệu | Xóa truyện tự động xóa toàn bộ chương (cascade delete) |
| NFR-03 | Validation | Backend validate dữ liệu đầu vào qua Pydantic; frontend validate qua Ant Design Form rules |
| NFR-04 | Thông báo lỗi | Lỗi từ API hiển thị ngay cho người dùng qua Alert context |
| NFR-05 | Pagination | Mặc định 20 bản ghi mỗi trang |
