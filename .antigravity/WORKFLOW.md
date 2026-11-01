# Quy trình làm việc bắt buộc (AI Workflow Rules)

> ⚠️ File này là **tập luật bắt buộc** cho AI assistant khi làm việc trong repo này.
> AI phải đọc file này ở đầu mỗi phiên và tuân thủ nghiêm ngặt.

---

## 📥 Khi bắt đầu phiên làm việc mới

1. **Đọc các file sau** theo thứ tự trước khi làm bất kỳ việc gì:
   - `.antigravity/progress/active_task.md` — nắm trạng thái hiện tại
   - `.antigravity/progress/backlog.md` — nắm danh sách việc cần làm (index)
   - Các file knowledge liên quan trong `.antigravity/knowledge/` nếu cần

2. **Thông báo** tóm tắt ngắn về trạng thái hiện tại cho người dùng.

---

## 🆕 Khi nhận một yêu cầu mới (BẮT BUỘC)

Mỗi yêu cầu từ người dùng phải được lưu thành **một file riêng** trong `.antigravity/progress/tasks/`.

> ⚠️ **QUAN TRỌNG:** Tạo file task **TRƯỚC KHI BẮT ĐẦU CODE**. Không được code trước rồi mới ghi task sau. Nếu không, task sẽ bị miss khi phiên làm việc gián đoạn.

### Bước 1 — Xác định số thứ tự
- Xem file cuối cùng trong thư mục `tasks/` để lấy số tiếp theo (ví dụ: file cuối là `006_...` → task mới là `007`).

### Bước 2 — Tạo file task mới NGAY LẬP TỨC
- Tên file: `NNN_ten_ngan_gon.md` (NNN là số 3 chữ số, ví dụ `007_ten_task.md`)
- Nội dung file bắt buộc theo mẫu sau:

```markdown
# Task #NNN — Tên đầy đủ của task

## 📋 Yêu cầu (Prompt)
> [Copy nguyên văn yêu cầu của người dùng]

## 📅 Thời gian
- Nhận: DD/MM/YYYY
- Hoàn thành: DD/MM/YYYY (điền khi xong)

## 🔧 Triển khai (Implementation)
[Mô tả các bước đã làm]

## 📁 Bằng chứng (Evidence)
- Files tạo mới: ...
- Files chỉnh sửa: ...
- Logic/thay đổi quan trọng: ...

## ✅ Trạng thái
**Đang thực hiện** / **Hoàn thành** / **Bị chặn**
```

### Bước 3 — Cập nhật `active_task.md`
- Ghi rõ task đang làm, trạng thái, các bước dự kiến.

### Bước 4 — Thêm vào index `backlog.md`
- Thêm dòng mới vào bảng "Chưa hoàn thành".

---

## ✅ Khi hoàn thành một nhiệm vụ (BẮT BUỘC)

### Bước 1 — Cập nhật file task (`tasks/NNN_...md`)
- Điền ngày hoàn thành vào phần `📅 Thời gian`.
- Điền đầy đủ phần `📁 Bằng chứng` (files đã tạo/chỉnh sửa, logic chính).
- Đổi `Trạng thái` → **Hoàn thành**.

### Bước 2 — Cập nhật `active_task.md`
- Đổi trạng thái thành ✅ hoàn thành.
- Ghi tóm tắt những gì đã làm.
- Cập nhật "Bước tiếp theo".
- Cập nhật dòng "*Cập nhật lần cuối*".

### Bước 3 — Cập nhật index `backlog.md`
- Chuyển task từ bảng "Chưa hoàn thành" → bảng "Đã hoàn thành".
- Thêm link đến file task tương ứng.

### Bước 4 — Xác nhận với người dùng
- Nói ngắn gọn: "Progress đã được cập nhật." ở cuối response.

---

## ❌ Những điều KHÔNG được làm

- Không hoàn thành một task rồi kết thúc turn mà **không** tạo/cập nhật file task
- Không để `active_task.md` ở trạng thái "đang làm" khi thực tế đã xong
- Không gộp nhiều yêu cầu khác nhau vào cùng một file task
- Không bỏ qua bước này dù task nhỏ đến đâu

---

## 📁 Cấu trúc thư mục `.antigravity/progress/`

```
progress/
├── active_task.md          # Task đang chạy trong phiên hiện tại
├── backlog.md              # Index tổng quan (trỏ đến tasks/)
└── tasks/                  # Một file = một yêu cầu
    ├── 001_ten_task.md
    ├── 002_ten_task.md
    └── NNN_ten_task.md
```

---

## 📝 Ghi chú

- File này được ưu tiên đọc hơn mọi hành vi mặc định khác.
- Người dùng có thể nhắc: *"Đọc WORKFLOW"* để AI refresh lại quy trình này.
- Người dùng có thể nhắc: *"Đọc `.antigravity/` và tiếp tục"* để bắt đầu phiên làm việc.
