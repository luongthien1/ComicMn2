# Task #005 — Thiết lập cơ chế automation cập nhật progress

## 📋 Yêu cầu (Prompt)
> "có cách nào để khiến bạn automation không?"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)
1. Giải thích các lớp automation khả thi (AI behavior rule, git hook, script).
2. Tạo `.antigravity/WORKFLOW.md` — file quy tắc bắt buộc cho AI, gồm:
   - Quy trình đầu phiên: đọc active_task + backlog trước khi làm việc
   - Quy trình cuối task: cập nhật active_task.md → backlog.md → xác nhận
   - Quy trình khi nhận task mới: thêm vào backlog + update active_task
   - Những điều KHÔNG được làm
3. Cập nhật `.antigravity/knowledge.md` (index) — thêm ghi chú ưu tiên đọc WORKFLOW.md.

## 📁 Bằng chứng (Evidence)
- File tạo mới: `e:\Code\Comic\ComicMn2\.antigravity\WORKFLOW.md`
- File chỉnh sửa: `e:\Code\Comic\ComicMn2\.antigravity\knowledge.md` — thêm ghi chú đầu file

## ✅ Trạng thái
**Hoàn thành**
