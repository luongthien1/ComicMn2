# Task #007 — Fix sidebar layout: tab lồi bị clip khi đóng

## 📋 Yêu cầu (Prompt)
> ".antigravity/ Tiếp tục 004 còn đang dở dang giúp tôi"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)

### Vấn đề phát hiện
Thiết kế cũ (Task #004) dùng `position: absolute; left: -37px` cho tab lồi — khi sidebar đóng (`width: 0`), wrapper div co lại và các tab bị **clip/overflow** ra ngoài viewport.

### Giải pháp
Thay đổi kiến trúc layout của `<Sidebar>`:
- **Trước:** Outer wrapper `position: relative`, tab buttons `position: absolute; left: -37px`
- **Sau:** Outer wrapper là flex row với `width: isOpen ? 287 : 37`, transition smooth. Tab buttons là cột bên trái (normal flow, 37px wide), sidebar panel là `flex: 1` bên phải.

### Chi tiết thay đổi
1. Outer wrapper: `width: isOpen ? 287 : 37`, `transition: width 0.2s cubic-bezier(...)` — tự co/dãn.
2. Tab column: `width: 37px`, `flexShrink: 0`, `flexDirection: column`, luôn hiển thị.
3. Sidebar panel: `flex: 1`, chỉ opacity + visibility transition (không còn width transition riêng).
4. Body container: bỏ `gap: sidebarOpen ? 16 : 0`, `paddingRight: sidebarOpen ? 0 : 36` — thay bằng `gap: 8` đơn giản (sidebar tự điều chỉnh width).
5. Xóa CSS không dùng: `.sidebar-tab-bar`, `.sidebar-tab-btn`, `.sidebar-tab-btn.active`, `.sidebar-tab-btn:hover` khỏi `editor.css`.

## 📁 Bằng chứng (Evidence)
- Files chỉnh sửa:
  - `e:\Code\Comic\ComicMn2\frontend\src\routes\Comics\ChapterEditor.tsx` — `Sidebar` component + body container
  - `e:\Code\Comic\ComicMn2\frontend\src\routes\Comics\editor.css` — xóa 32 dòng CSS cũ

## ✅ Trạng thái
**Hoàn thành**
