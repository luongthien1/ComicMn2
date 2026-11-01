# Task #003 — Chatbot UI cho tính năng Hỏi đáp (Q&A)

## 📋 Yêu cầu (Prompt)
> "Phần UI hỏi đáp, bạn có thể làm giống như chatbot UI được không?"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)
1. Phân tích component `QATab` cũ trong `ChapterEditor.tsx` — giao diện dạng danh sách đơn giản.
2. Thiết kế lại hoàn toàn thành Chatbot UI:
   - **Câu hỏi (User):** Bubble căn phải, nền đen (→ sau đổi monochrome), avatar người dùng.
   - **Câu trả lời (Bot):** Bubble căn trái, nền trắng, avatar robot xám.
   - Ô nhập câu hỏi ở dưới cùng kiểu chat input + nút Send tròn.
   - Sau khi gửi câu hỏi → **tự động mở ô trả lời** (inline edit mode).
   - Click vào bubble trả lời để chỉnh sửa trực tiếp.
   - Click dấu `+` (placeholder) để thêm câu trả lời cho câu hỏi chưa có.
   - Auto-scroll xuống cuối khi có tin nhắn mới.
3. Thêm imports mới: `RobotOutlined`, `SendOutlined`, `UserOutlined`, `CheckOutlined`, `CloseOutlined`, `EditOutlined`, `Avatar`.
4. Data vẫn lưu vào `localStorage` qua `ls.saveQA()` — không thay đổi storage logic.

## 📁 Bằng chứng (Evidence)
- File chỉnh sửa: `e:\Code\Comic\ComicMn2\frontend\src\routes\Comics\ChapterEditor.tsx`
  - Thay thế toàn bộ `QATab` component (dòng ~217–273 → ~217–416)
  - Thêm `useRef`, `useEffect` cho auto-scroll
  - Thêm state: `inputVal`, `editingId`, `editAnswerVal`
  - Logic mới: `handleSendQuestion()`, `startEditing()`, `saveAnswer()`

## ✅ Trạng thái
**Hoàn thành**
