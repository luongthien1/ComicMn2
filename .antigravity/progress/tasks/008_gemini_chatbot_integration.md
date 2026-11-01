# Task #008 — Tích hợp Gemini AI vào Chatbot Q&A

## 📋 Yêu cầu (Prompt)
> "Tôi đã thêm GEMINI_API_KEY vào env, giờ hãy viết code để tôi có thể chat bằng gemini trong ui chatbot vừa sửa"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🗺️ Kế hoạch triển khai

### Backend
1. Thêm `GEMINI_API_KEY` vào `core/config.py` (Settings class).
2. Tạo `api/ai/` router — endpoint `POST /api/ai/chat` nhận `{ messages }` và trả về câu trả lời từ Gemini.
3. Cài thêm package `google-generativeai` vào backend dependencies.

### Frontend
4. Tạo `frontend/src/api/ai/index.ts` — API client gửi yêu cầu đến `/api/ai/chat`.
5. Cập nhật `QATab` trong `ChapterEditor.tsx`:
   - Gửi tin nhắn đồng thời gọi API hỏi Gemini.
   - Thêm trạng thái `loadingId` để hiển thị spinner bubble với text "Gemini đang trả lời..." khi chờ API phản hồi.
   - Điền tự động câu trả lời vào chatbot bubble, và người dùng vẫn có thể click vào để sửa thủ công nếu muốn.

## 📁 Bằng chứng (Evidence)
- **Backend files modified/added:**
  - `backend/core/config.py` (Thêm `GEMINI_API_KEY: str = ""`)
  - `backend/api/ai.py` (Mới: logic cấu hình `gemini-2.5-flash` và endpoint `/chat`)
  - `backend/api/__init__.py` (Đăng ký `/ai` prefix router)
- **Frontend files modified/added:**
  - `frontend/src/api/ai/index.ts` (Mới: class `AiApi` kế thừa `BaseApi`)
  - `frontend/src/routes/Comics/ChapterEditor.tsx` (Tích hợp `askGemini` và render loading state bubble)
- **Testing:**
  - Viết script test `test_gemini.py` gọi trực tiếp API key từ config và model `gemini-2.5-flash`, kết quả phản hồi bằng Tiếng Việt thành công.

## ✅ Trạng thái
**Hoàn thành**
