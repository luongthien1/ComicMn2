# Task #006 — Tái cấu trúc Backlog: mỗi yêu cầu một file riêng

## 📋 Yêu cầu (Prompt)
> "Tại sao backlog là một file? Với mỗi yêu cầu của tôi, vui lòng lưu một file. Có prompt, kết quả thực hiện, bằng chứng giúp tôi. (cập nhật vào file hướng dẫn để agent sau làm việc)"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)
1. Tạo thư mục `.antigravity/progress/tasks/` để lưu từng task thành file riêng.
2. Migrate toàn bộ các task đã hoàn thành từ `backlog.md` sang file riêng:
   - `001_setup_antigravity_system.md`
   - `002_run_guide_documentation.md`
   - `003_chatbot_qa_ui.md`
   - `004_sidebar_right_protruding_tabs_monochrome.md`
   - `005_automation_workflow_setup.md`
   - `006_restructure_tasks_per_file.md` (file này)
3. Cập nhật `backlog.md` → chỉ còn là **Index** trỏ đến task files.
4. Cập nhật `WORKFLOW.md` → bổ sung quy tắc tạo task file cho mỗi yêu cầu mới.
5. Format mỗi task file gồm: Prompt, Thời gian, Triển khai, Bằng chứng, Trạng thái.

## 📁 Bằng chứng (Evidence)
- Thư mục mới: `.antigravity/progress/tasks/`
- Files tạo mới: `001` đến `006` trong thư mục trên
- Files chỉnh sửa: `backlog.md`, `WORKFLOW.md`

## ✅ Trạng thái
**Hoàn thành**
