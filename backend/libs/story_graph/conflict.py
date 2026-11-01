"""Kiểm mâu thuẫn: so đoạn nháp mới với truyện đã viết.

Khác tra cứu (`retriever.py`): ở đó tìm thông tin CÓ trong truyện; ở đây so
đoạn MỚI với truyện cũ tại một thời điểm cụ thể.

Đo trên 10 ca thử, 6 lần chạy (research/notes/16):

    trung bình      9.2/10
    bắt mâu thuẫn   6/6 ở mọi lần chạy
    báo động giả    0-1 mỗi lần

Phần bắt mâu thuẫn ổn định; dao động nằm ở báo động giả. Với công cụ viết truyện
đó là đúng hướng — không bỏ sót, chỉ đôi khi quá nhạy.
"""

from __future__ import annotations

import json
import logging
import re

import httpx
from core.ai_config import get_ollama

from .retriever import get_retriever

logger = logging.getLogger(__name__)

# Quy tắc 2 gộp từ hai quy tắc rời từng xung đột nhau: model coi "nhắc lại lời
# X dạy" là hành động của X rồi báo mâu thuẫn (research/notes/16 vòng 2).
SYSTEM_CHECK = (
    "Bạn là trợ lý kiểm tra tính nhất quán cho người viết truyện.\n"
    "Bạn nhận: SỰ THẬT TỪ ĐỒ THỊ (đã kiểm chứng), ĐOẠN TRÍCH từ truyện đã viết, "
    "và một ĐOẠN NHÁP MỚI mà tác giả định chèn vào một chương cụ thể.\n\n"
    "Nhiệm vụ: xác định đoạn nháp có MÂU THUẪN với truyện đã viết không.\n\n"
    "QUY TẮC:\n"
    "1. Chỉ báo mâu thuẫn khi có BẰNG CHỨNG rõ ràng. Không suy đoán.\n"
    "2. Phân biệt HÀNH ĐỘNG TRỰC TIẾP với NHẮC ĐẾN:\n"
    "   - Nhân vật HÀNH ĐỘNG trong cảnh (nói, đi, đánh) tại chương họ CHƯA xuất hiện "
    "-> ĐÓ LÀ mâu thuẫn.\n"
    "   - Nhân vật chỉ được NHẮC ĐẾN, nhớ lại, hồi tưởng, hoặc kể về quá khứ "
    "-> KHÔNG phải mâu thuẫn, kể cả khi họ không còn xuất hiện ở chương đó.\n"
    "   Ví dụ: 'Tôi nhớ lại lời X dạy năm xưa' là HỢP LỆ ở mọi chương sau khi X đã "
    "xuất hiện, vì X không hành động trong hiện tại.\n"
    "3. Chỉ số (cấp độ, Hp) đi ngược tiến trình -> ĐÓ LÀ mâu thuẫn.\n"
    "4. Sự thật THAY ĐỔI theo chương (tên gọi, trạng thái). Đọc KỸ cả mốc thời gian "
    "trong dữ liệu đồ thị trước khi kết luận — đừng chỉ đọc nửa đầu.\n"
    "5. BẮT BUỘC so sánh số chương trước khi kết luận. Với mỗi nhân vật trong đoạn "
    "nháp, làm đúng phép so sánh này:\n"
    "   - Gọi F = chương nhân vật xuất hiện lần đầu (đồ thị cho biết).\n"
    "   - Gọi N = chương đang xét.\n"
    "   - Nếu N >= F: HỢP LỆ. Nhân vật đã tồn tại và giữ mọi thuộc tính (tên gọi, "
    "quan hệ) từ F trở về sau. TUYỆT ĐỐI không báo mâu thuẫn.\n"
    "   - Chỉ khi N < F mới là mâu thuẫn.\n"
    "   Ví dụ: Hari có F=21. Đoạn nháp ở chương 22 -> 22 >= 21 -> HỢP LỆ, dù tên "
    "Hari mới có từ chương 21.\n"
    "6. Nếu dòng 'Chương N có mặt: …' liệt kê một nhân vật, thì nhân vật đó CÓ mặt "
    "ở chương N — đừng kết luận ngược lại.\n"
    "7. Báo động giả rất tai hại. Không chắc thì nói không phát hiện mâu thuẫn.\n\n"
    'Chỉ trả JSON: {"conflict": true|false, "reason": "giải thích ngắn", '
    '"evidence_chapters": [số chương]}'
)


def _ask(prompt: str) -> str:
    cfg = get_ollama()
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_CHECK},
            {"role": "user", "content": prompt},
        ],
        "think": False,
        "stream": False,
        "options": {"num_ctx": 16384},
    }
    r = httpx.post(
        f"{cfg.base_url}/api/chat",
        json=payload,
        headers=cfg.headers,
        timeout=cfg.timeout,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _parse(raw: str) -> dict:
    """Đọc kết luận, chịu được JSON bị cắt.

    Model đôi khi viết reason dài rồi hết token, JSON không đóng ngoặc.
    Lúc đó vẫn đọc được `"conflict": true` — lỗi parse không phải lỗi suy luận.
    """
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            d = json.loads(m.group())
            return {
                "conflict": bool(d.get("conflict")),
                "reason": str(d.get("reason", ""))[:800],
                "evidence_chapters": d.get("evidence_chapters") or [],
                "truncated": False,
            }
        except json.JSONDecodeError:
            pass

    m2 = re.search(r'"conflict"\s*:\s*(true|false)', raw, re.I)
    if m2:
        m3 = re.search(r'"reason"\s*:\s*"([^"]{0,800})', raw)
        return {
            "conflict": m2.group(1).lower() == "true",
            "reason": (m3.group(1) if m3 else raw[:300]),
            "evidence_chapters": [],
            "truncated": True,
        }

    return {
        "conflict": None,
        "reason": f"Không đọc được kết luận từ model: {raw[:200]}",
        "evidence_chapters": [],
        "truncated": True,
    }


def check_draft(
    draft: str,
    at_chapter: float,
    comic_id: int,
    k: int = 6,
) -> dict:
    """Kiểm một đoạn nháp có mâu thuẫn với truyện đã viết không."""
    if not get_ollama().configured:
        return {"available": False, "error": "Chưa cấu hình Ollama (trang Cài đặt hoặc .env)."}

    retriever = get_retriever()

    # Truy hồi bằng chính nội dung nháp — đó là thứ cần đối chiếu
    ctx = retriever.retrieve(draft, chapter=None, comic_id=comic_id, k=k)
    if not ctx.available:
        return {"available": False, "error": ctx.error}

    facts = ctx.facts
    driver = retriever._get_driver()
    if driver is not None:
        try:
            with driver.session() as s:
                extra = retriever._facts(s, draft, float(at_chapter), comic_id)
            if extra and extra not in facts:
                facts += extra
        except Exception as e:
            logger.warning("Không lấy được sự thật theo chương: %s", e)

    chunks = "\n\n".join(
        f"[ch.{c['chapter']:g}] {c['text'][:600]}" for c in ctx.chunks[:5]
    )
    prompt = (
        f"{facts}ĐOẠN TRÍCH TỪ TRUYỆN ĐÃ VIẾT:\n\n{chunks}\n\n"
        f"---\nĐOẠN NHÁP MỚI (tác giả định chèn vào CHƯƠNG {at_chapter:g}):\n\n"
        f"{draft}\n\n"
        f"Đoạn nháp này có mâu thuẫn với truyện đã viết không?"
    )

    try:
        result = _parse(_ask(prompt))
    except Exception as e:
        logger.exception("Kiểm mâu thuẫn hỏng")
        return {"available": False, "error": str(e)}

    return {
        "available": True,
        **result,
        "chapters_checked": ctx.chapters_used,
        "had_facts": bool(facts),
    }
