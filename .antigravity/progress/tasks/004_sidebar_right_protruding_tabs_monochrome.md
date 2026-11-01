# Task #004 — Sidebar phải + Tab lồi toggle + Hệ màu đen-xám-trắng

## 📋 Yêu cầu (Prompt)
> "Phần mềm này nên chỉ có các màu, đen xám và trắng."
> "Ngoài ra, chuyển sidebar trong page viết truyện sang bên phải giúp tôi."
> "Các tab không để trên đầu nữa, mà nằm 'chìa' một phần ra bên trái của sidebar. Nó sẽ là nút toggle đóng mở sidebar, vừa là nó chuyển tab."

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)

### 1. Sidebar chuyển sang phải
- Trong `ChapterEditor()` render: đặt `<Editor>` trước `<Sidebar>` trong flex layout.
- Thêm state `sidebarOpen` (default `true`) vào `ChapterEditor`.
- Truyền `isOpen` và `setIsOpen` xuống `Sidebar` component.

### 2. Tab lồi (protruding tabs)
- Xóa `className="sidebar-tab-bar"` cũ.
- Tạo div tuyệt đối (position absolute) `left: "-37px"` — chìa ra ngoài bên trái sidebar.
- Mỗi tab là `<button>` icon 36×36px, bo góc `6px 0 0 6px` (chỉ bo bên trái).
- **Logic toggle:** Click cùng tab đang active → đóng/mở sidebar. Click tab khác → chuyển tab + mở sidebar.
- Tab active: nền đen `#000`, chữ trắng, border-right bị ẩn (để liền với sidebar panel).
- Kèm `<Tooltip placement="left">` hiển thị tên tab khi hover.
- Tab icons: `PictureOutlined` (Ảnh), `BookOutlined` (Chương), `EditOutlined` (Ghi chú), `MessageOutlined` (Hỏi đáp).

### 3. Sidebar panel có header
- Header gồm: tên tab đang active + nút `X` đóng.
- Animation `width` transition `0.2s cubic-bezier(...)` khi đóng/mở.
- Khi đóng (`width: 0`): opacity về 0, visibility hidden.

### 4. Hệ màu Đen - Xám - Trắng
| Thành phần | Trước | Sau |
|---|---|---|
| Toolbar active buttons | `type="primary"` (xanh dương) | `backgroundColor: #000`, `color: #fff` |
| Chat bubble câu hỏi | `#1677ff` (xanh) | `#000` (đen) |
| Avatar User | `#87d068` (xanh lá) | `#262626` (đen xám) |
| Avatar Bot | `#1677ff` (xanh dương) | `#595959` (xám) |
| Nút Lưu (Save) | `type="primary"` (xanh) | `backgroundColor: #000` |
| Nút Send | `type="primary"` (xanh) | `backgroundColor: #000` |
| Nút Lưu trong edit-answer | `type="primary"` (xanh) | `backgroundColor: #000` |
| Active chapter trong ChaptersTab | `#e6f4ff` / `#1677ff` | `#f0f0f0` / `#000` |
| ProseMirror selected node | `#1677ff` | `#000` |

## 📁 Bằng chứng (Evidence)
- Files chỉnh sửa:
  - `e:\Code\Comic\ComicMn2\frontend\src\routes\Comics\ChapterEditor.tsx` — toàn bộ Sidebar + QATab + Toolbar + ChapterEditor component
  - `e:\Code\Comic\ComicMn2\frontend\src\routes\Comics\editor.css` — ProseMirror outline color
- Imports thêm mới: `BookOutlined`, `MessageOutlined`
- State mới trong `ChapterEditor`: `sidebarOpen: boolean`
- Props mới trong `Sidebar`: `isOpen`, `setIsOpen`

## ✅ Trạng thái
**Hoàn thành**
