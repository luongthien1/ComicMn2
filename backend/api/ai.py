from typing import List

import google.generativeai as genai
import httpx
from core.config import settings
from db.model.chapter import Chapter
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from libs.database.connect import get_db
from libs.story_graph import get_retriever
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()

genai.configure(api_key=settings.GEMINI_API_KEY)

# System prompt khi có tư liệu truyện. Ba quy tắc đầu đến từ thử nghiệm:
# - quy tắc 2: sự thật trong truyện THAY ĐỔI theo chương (research/notes/12)
# - quy tắc 4: trích dẫn để người viết kiểm chứng (research/notes/01)
# - quy tắc 5: qwen3.5 hay rò chữ Hán khi bí (research/notes/01)
GROUNDED_PROMPT = (
    "Bạn là trợ lý AI hỗ trợ người viết truyện.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. SỰ THẬT TỪ ĐỒ THỊ đã được kiểm chứng cơ học — tin cậy hơn đoạn trích. "
    "Nếu đoạn trích nói ngược lại, nêu cả hai và chỉ ra mâu thuẫn.\n"
    "2. Nhiều sự thật trong truyện THAY ĐỔI theo thời gian. Nếu câu hỏi không nêu "
    "mốc chương mà đáp án phụ thuộc thời điểm, hãy nêu ĐẦY ĐỦ các mốc.\n"
    "3. Không suy đoán. Không có thông tin thì nói rõ là không tìm thấy trong tư liệu.\n"
    "4. Luôn dẫn số chương dạng [ch.N] cho mỗi thông tin lấy từ tư liệu.\n"
    "5. Trả lời HOÀN TOÀN bằng tiếng Việt, không dùng chữ Hán."
)


class Message(BaseModel):
    role: str   # "user" or "model"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    system_prompt: str = (
        "Bạn là trợ lý AI hỗ trợ người viết truyện. "
        "Hãy trả lời ngắn gọn, súc tích và hữu ích bằng tiếng Việt."
    )
    provider: str | None = None   # ghi đè AI_PROVIDER cho từng request

    # Tra cứu truyện từ graph. Bỏ trống comic_id thì tắt tra cứu.
    comic_id: int | None = None
    chapter: float | None = None   # chương đang mở, để giới hạn phạm vi


class RetrievalInfo(BaseModel):
    """Cho UI biết câu trả lời dựa trên gì — để người viết kiểm chứng."""

    used: bool
    route: str | None = None
    chapters: List[float] = []
    n_chunks: int = 0
    n_scenes: int = 0
    had_facts: bool = False
    note: str | None = None
    # Mã để xem toàn bộ quá trình suy luận: GET /api/ai/story-graph/trace/{id}
    trace_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    provider: str
    retrieval: RetrievalInfo | None = None


async def _chat_gemini(req: ChatRequest) -> str:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY chưa được cấu hình.")

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=req.system_prompt,
    )

    # Build history for multi-turn (all but last message)
    history = []
    for msg in req.messages[:-1]:
        history.append({
            "role": msg.role,
            "parts": [msg.content],
        })

    chat_session = model.start_chat(history=history)
    last_msg = req.messages[-1].content
    response = chat_session.send_message(last_msg)
    return response.text


async def _chat_ollama(req: ChatRequest) -> str:
    if not settings.OLLAMA_TOKEN:
        raise HTTPException(status_code=500, detail="OLLAMA_TOKEN chưa được cấu hình.")

    # Gemini dùng role "model", Ollama dùng "assistant"
    messages = [{"role": "system", "content": req.system_prompt}]
    for msg in req.messages:
        role = "assistant" if msg.role == "model" else msg.role
        messages.append({"role": role, "content": msg.content})

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "think": False,   # qwen3.5 bật thinking mặc định, không tắt thì trace lẫn vào câu trả lời
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
                headers={"Authorization": f"Bearer {settings.OLLAMA_TOKEN}"},
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Không kết nối được máy chạy Ollama ({settings.OLLAMA_BASE_URL}): {e}",
            )

    if resp.status_code == 401:
        raise HTTPException(status_code=500, detail="OLLAMA_TOKEN không đúng.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Ollama trả về {resp.status_code}: {resp.text[:200]}")

    return resp.json()["message"]["content"]


def _ground_in_story(req: ChatRequest) -> tuple[ChatRequest, RetrievalInfo, object]:
    """Chèn tư liệu truyện vào câu hỏi cuối, nếu bật tra cứu.

    Trả về (request đã sửa, thông tin nguồn, recorder). Recorder giữ lại để
    ghi nốt câu trả lời sau khi LLM trả về.
    Nếu graph không sẵn sàng thì trả nguyên request — chat vẫn chạy.
    """
    from libs.story_graph.trace import TraceRecorder

    if req.comic_id is None or not req.messages:
        return req, RetrievalInfo(used=False), None

    question = req.messages[-1].content
    rec = TraceRecorder(question, req.comic_id, req.chapter)
    ctx = get_retriever().retrieve(question, req.chapter, req.comic_id, rec=rec)

    if not ctx.available:
        rec.finish(answer=None)
        return req, RetrievalInfo(used=False, note=ctx.error, trace_id=rec.trace.id), None

    block = ctx.to_prompt_block()
    if not block:
        rec.finish(answer=None)
        return req, RetrievalInfo(
            used=False, route=ctx.route, trace_id=rec.trace.id,
            note="Không tìm thấy tư liệu liên quan trong truyện.",
        ), None

    grounded = req.model_copy(deep=True)
    grounded.system_prompt = GROUNDED_PROMPT
    tail = (
        f"Câu hỏi về chương {ctx.chapter:g}: {question}"
        if ctx.chapter is not None
        else f"Câu hỏi: {question}"
    )
    grounded.messages[-1].content = f"{block}---\n{tail}"

    return grounded, RetrievalInfo(
        used=True,
        route=ctx.route,
        chapters=ctx.chapters_used,
        n_chunks=len(ctx.chunks),
        n_scenes=len(ctx.scenes),
        had_facts=bool(ctx.facts),
        trace_id=rec.trace.id,
    ), rec


@router.get("/story-graph/stats")
def story_graph_stats(comic_id: int = 1):
    """Trạng thái graph — UI dùng để biết đã ingest truyện chưa."""
    return get_retriever().stats(comic_id)


class ConflictCheckRequest(BaseModel):
    """Kiểm một đoạn nháp có mâu thuẫn với truyện đã viết không."""

    draft: str
    at_chapter: float
    comic_id: int = 1


@router.post("/story-graph/check-conflict")
def story_graph_check_conflict(req: ConflictCheckRequest):
    """So đoạn nháp mới với truyện cũ tại một thời điểm cụ thể.

    Khác /chat: ở đây không trả lời câu hỏi mà tìm mâu thuẫn.
    Đo được 9.2/10 trên 10 ca thử, 6 lần chạy (research/notes/16).
    """
    from libs.story_graph.conflict import check_draft

    if not req.draft.strip():
        raise HTTPException(status_code=400, detail="Đoạn nháp trống.")

    result = check_draft(req.draft, req.at_chapter, req.comic_id)
    if not result.get("available"):
        raise HTTPException(
            status_code=503,
            detail=result.get("error") or "Không kiểm được mâu thuẫn.",
        )
    return result


class ReviewRequest(BaseModel):
    """Đánh giá truyện hoặc một chương."""

    comic_id: int = 1
    # Bỏ trống -> đánh giá toàn truyện; có số -> đánh giá chương đó
    chapter: float | None = None
    # Bỏ trống -> đánh giá mọi khía cạnh
    aspects: List[str] | None = None


@router.get("/story-graph/review-aspects")
def story_graph_review_aspects():
    """Các khía cạnh đánh giá — UI dùng để dựng checkbox."""
    from libs.story_graph.review import ASPECTS

    return {
        "aspects": [
            {"key": k, "label": v["label"], "guide": v["guide"]}
            for k, v in ASPECTS.items()
        ]
    }


@router.post("/story-graph/review")
def story_graph_review(req: ReviewRequest):
    """Nhận xét chất lượng truyện — nhịp, nhân vật, văn phong…

    Khác /chat (trả lời câu hỏi) và /check-conflict (tìm mâu thuẫn):
    đây là đánh giá có dẫn chứng, kèm gợi ý sửa.

    Số liệu đếm được lấy từ graph bằng Cypher, không để LLM đoán.
    """
    from libs.story_graph.review import review_chapter, review_story

    result = (
        review_chapter(req.chapter, req.comic_id, req.aspects)
        if req.chapter is not None
        else review_story(req.comic_id, req.aspects)
    )
    if not result.get("available"):
        raise HTTPException(
            status_code=503,
            detail=result.get("error") or "Không đánh giá được.",
        )
    return result


@router.get("/story-graph/ingest-progress")
def story_graph_ingest_progress(comic_id: int = 1):
    """Tiến độ nạp truyện — UI hỏi định kỳ trong lúc chạy."""
    from libs.story_graph.ingest import get_progress

    return get_progress(comic_id)


@router.post("/story-graph/ingest")
def story_graph_ingest(
    comic_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Nạp toàn bộ chương của truyện vào đồ thị tri thức.

    Chạy nền vì phải embedding từng chunk (vài phút cho truyện dài).
    Hỏi tiến độ qua /story-graph/ingest-progress.
    """
    from libs.story_graph.ingest import get_progress, run_ingest, strip_html

    if not settings.NEO4J_URI:
        raise HTTPException(status_code=503, detail="NEO4J_URI chưa được cấu hình.")
    if not settings.OLLAMA_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="OLLAMA_TOKEN chưa được cấu hình — không tạo được embedding.",
        )
    if get_progress(comic_id).get("running"):
        raise HTTPException(status_code=409, detail="Đang nạp truyện này rồi.")

    rows = (
        db.query(Chapter)
        .filter(Chapter.comic_id == comic_id)
        .order_by(Chapter.number)
        .all()
    )
    chapters = [
        {"number": float(c.number), "title": c.title or "", "text": strip_html(c.content or "")}
        for c in rows
    ]
    chapters = [c for c in chapters if len(c["text"]) > 50]

    if not chapters:
        raise HTTPException(
            status_code=400,
            detail="Truyện chưa có chương nào đủ nội dung để nạp.",
        )

    background_tasks.add_task(run_ingest, comic_id, chapters)
    return {"started": True, "chapters": len(chapters)}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    provider = (req.provider or settings.AI_PROVIDER).lower()

    if provider not in ("gemini", "ollama"):
        raise HTTPException(status_code=400, detail=f"Provider không hợp lệ: {provider}")

    req, retrieval, rec = _ground_in_story(req)

    try:
        if provider == "ollama":
            answer = await _chat_ollama(req)
        else:
            answer = await _chat_gemini(req)
    except HTTPException:
        raise
    except Exception as e:
        if rec is not None:
            rec.finish(prompt=req.messages[-1].content, answer=f"[LỖI] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if rec is not None:
        rec.finish(prompt=req.messages[-1].content, answer=answer)

    return ChatResponse(answer=answer, provider=provider, retrieval=retrieval)


@router.get("/story-graph/trace/{trace_id}")
def story_graph_trace(trace_id: str):
    """Toàn bộ quá trình suy luận của một lần chat.

    Gồm: định tuyến và lý do, từng truy vấn Cypher kèm tham số và kết quả,
    prompt cuối gửi cho LLM, và câu trả lời.
    """
    from libs.story_graph.trace import get_trace

    trace = get_trace(trace_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy trace — chỉ giữ 50 lần gần nhất, và mất khi backend khởi động lại.",
        )
    return trace


@router.get("/story-graph/traces")
def story_graph_traces(comic_id: int | None = None, limit: int = 20):
    """Danh sách trace gần đây, để mở tab xem lại."""
    from libs.story_graph.trace import list_traces

    return {"traces": list_traces(comic_id, limit)}
