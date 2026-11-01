"""Đánh giá truyện — nhận xét một chương hoặc toàn truyện.

Khác hai chức năng đã có:

  chat          trả lời câu hỏi về truyện
  check-conflict tìm mâu thuẫn trong đoạn nháp
  review        NHẬN XÉT chất lượng: nhịp truyện, nhân vật, điểm mạnh/yếu

Đánh giá là việc chủ quan, nên thiết kế theo hai nguyên tắc:

1. **Dẫn chứng bắt buộc.** Mỗi nhận xét phải kèm trích dẫn [ch.N]. Nhận xét
   chung chung ("truyện hay") vô dụng với người viết.

2. **Không bịa số liệu.** Những gì đếm được (số chương, nhân vật xuất hiện bao
   nhiêu chương, độ dài) lấy từ graph bằng Cypher, không để LLM đoán —
   research/notes/05: đếm chuỗi là việc máy làm chính xác 100%.
"""

from __future__ import annotations

import json
import logging
import re

import httpx
from core.ai_config import get_ollama

from .retriever import get_retriever

logger = logging.getLogger(__name__)

# Các khía cạnh đánh giá. Mỗi khía cạnh có hướng dẫn riêng để nhận xét
# bám vào thứ cụ thể thay vì cảm tính chung chung.
ASPECTS = {
    "pacing": {
        "label": "Nhịp truyện",
        "guide": "Chương nào dài dòng, chương nào dồn dập? Có chương nào không đẩy "
                 "cốt truyện đi đâu không? Cao trào đặt ở đâu?",
    },
    "character": {
        "label": "Nhân vật",
        "guide": "Nhân vật có động cơ rõ không? Ai xuất hiện rồi biến mất không lý do? "
                 "Tính cách có nhất quán không?",
    },
    "worldbuilding": {
        "label": "Xây dựng thế giới",
        "guide": "Quy tắc thế giới có được giải thích đủ không? Có chỗ nào mâu thuẫn "
                 "với quy tắc đã đặt ra? Thông tin có bị dồn quá nhiều một lúc không?",
    },
    "prose": {
        "label": "Văn phong",
        "guide": "Câu văn có lặp mẫu không? Đối thoại tự nhiên không? Mô tả có thừa "
                 "hay thiếu chỗ nào?",
    },
    "structure": {
        "label": "Cấu trúc",
        "guide": "Mở đầu có hút không? Chuyển cảnh mượt không? Kết chương có lý do "
                 "để đọc tiếp không?",
    },
}

SYSTEM_REVIEW = (
    "Bạn là biên tập viên giàu kinh nghiệm, đang đọc bản thảo của một người viết truyện.\n\n"
    "NHIỆM VỤ: đưa nhận xét THẲNG THẮN và CỤ THỂ để họ sửa được.\n\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Mỗi nhận xét PHẢI kèm dẫn chứng cụ thể từ tư liệu, ghi rõ [ch.N]. "
    "Nhận xét không có dẫn chứng thì bỏ đi, đừng viết.\n"
    "2. Nêu cả điểm mạnh lẫn điểm yếu. Nhưng đừng khen chung chung — nói rõ "
    "đoạn nào hiệu quả và VÌ SAO.\n"
    "3. Với mỗi điểm yếu, gợi ý hướng sửa cụ thể.\n"
    "4. SỐ LIỆU THỐNG KÊ đã cho sẵn là chính xác — dùng chúng, đừng tự đếm lại "
    "hay đoán.\n"
    "5. Chỉ nhận xét dựa trên tư liệu được cung cấp. Không suy đoán về phần "
    "truyện bạn chưa đọc — nếu tư liệu thiếu, nói rõ là thiếu.\n"
    "6. Trả lời HOÀN TOÀN bằng tiếng Việt, không dùng chữ Hán.\n\n"
    "ĐỊNH DẠNG: trả về JSON:\n"
    '{"summary": "2-3 câu tóm tắt ấn tượng chung",\n'
    ' "strengths": [{"point": "...", "evidence": "[ch.N] trích dẫn hoặc mô tả cụ thể"}],\n'
    ' "issues": [{"point": "...", "evidence": "[ch.N] ...", "suggestion": "hướng sửa"}],\n'
    ' "score": {"pacing": 1-5, "character": 1-5, "worldbuilding": 1-5, '
    '"prose": 1-5, "structure": 1-5}}'
)


# ---------------------------------------------------------------- thống kê

Q_CHAPTER_STATS = """
    MATCH (c:Chapter {comic_id: $cid})
    OPTIONAL MATCH (c)-[:HAS_CHUNK]->(ck:Chunk)
    WITH c, count(ck) AS n_chunks, sum(size(ck.text)) AS chars
    RETURN c.number AS number, c.title AS title, n_chunks, coalesce(chars, 0) AS chars
    ORDER BY c.number
"""

Q_ENTITY_SPREAD = """
    MATCH (e:Entity {comic_id: $cid})
    WHERE e.n_chapters IS NOT NULL
    RETURN e.name AS name, e.first_ch AS first_ch, e.last_ch AS last_ch,
           e.n_chapters AS n_chapters
    ORDER BY e.n_chapters DESC LIMIT 20
"""

Q_ONE_CHAPTER = """
    MATCH (c:Chapter {comic_id: $cid, number: $ch})-[:HAS_CHUNK]->(ck:Chunk)
    RETURN ck.text AS text, ck.offset AS offset
    ORDER BY ck.offset
"""

Q_CHAPTER_ENTITIES = """
    MATCH (e:Entity {comic_id: $cid})-[:APPEARS_IN]->(c:Chapter {comic_id: $cid, number: $ch})
    RETURN e.name AS name, e.first_ch AS first_ch ORDER BY e.name
"""

Q_CHAPTER_SCENES = """
    MATCH (c:Chapter {comic_id: $cid, number: $ch})-[:HAS_SCENE]->(s:Scene)
    OPTIONAL MATCH (s)-[:HAS_MOOD]->(m:Mood)
    RETURN s.summary AS summary, s.key_action AS key_action,
           collect(DISTINCT m.name) AS moods, s.order AS ord
    ORDER BY s.order
"""


def _collect_stats(session, comic_id: int) -> dict:
    """Số liệu đếm được — KHÔNG để LLM tự đoán (research/notes/05)."""
    chapters = session.run(Q_CHAPTER_STATS, cid=comic_id).data()
    entities = session.run(Q_ENTITY_SPREAD, cid=comic_id).data()

    if not chapters:
        return {}

    lens = [c["chars"] for c in chapters if c["chars"]]
    avg = sum(lens) / len(lens) if lens else 0

    # Chương lệch nhiều so với trung bình — đáng để biên tập viên nhìn
    outliers_long = [c for c in chapters if c["chars"] > avg * 1.6]
    outliers_short = [c for c in chapters if 0 < c["chars"] < avg * 0.5]

    # Nhân vật chỉ xuất hiện rồi biến mất sớm
    vanished = [
        e for e in entities
        if e["n_chapters"] <= 3 and e["last_ch"] < max(c["number"] for c in chapters) - 10
    ]

    return {
        "n_chapters": len(chapters),
        "total_chars": sum(lens),
        "avg_chars": round(avg),
        "longest": sorted(chapters, key=lambda c: -c["chars"])[:3],
        "shortest": [c for c in sorted(chapters, key=lambda c: c["chars"]) if c["chars"]][:3],
        "outliers_long": [c["number"] for c in outliers_long],
        "outliers_short": [c["number"] for c in outliers_short],
        "top_entities": entities[:10],
        "vanished_entities": vanished[:5],
    }


def _format_stats(stats: dict) -> str:
    if not stats:
        return ""
    lines = [
        "SỐ LIỆU (đếm cơ học từ đồ thị, CHÍNH XÁC — dùng trực tiếp, đừng tự đếm lại):",
        f"- Tổng: {stats['n_chapters']} chương, {stats['total_chars']:,} ký tự, "
        f"trung bình {stats['avg_chars']:,} ký tự/chương.",
    ]
    if stats.get("longest"):
        longest = ", ".join(
            f"ch.{c['number']:g} ({c['chars']:,})" for c in stats["longest"]
        )
        lines.append(f"- Chương dài nhất: {longest}.")
    if stats.get("shortest"):
        shortest = ", ".join(
            f"ch.{c['number']:g} ({c['chars']:,})" for c in stats["shortest"]
        )
        lines.append(f"- Chương ngắn nhất: {shortest}.")
    if stats.get("outliers_long"):
        chs = ", ".join(f"{c:g}" for c in stats["outliers_long"][:8])
        lines.append(f"- Chương dài bất thường (>1.6× trung bình): {chs}.")
    if stats.get("outliers_short"):
        chs = ", ".join(f"{c:g}" for c in stats["outliers_short"][:8])
        lines.append(f"- Chương ngắn bất thường (<0.5× trung bình): {chs}.")
    if stats.get("top_entities"):
        ents = ", ".join(
            f"{e['name']} ({e['n_chapters']} chương, ch.{e['first_ch']:g}–{e['last_ch']:g})"
            for e in stats["top_entities"][:8]
        )
        lines.append(f"- Nhân vật xuất hiện nhiều nhất: {ents}.")
    if stats.get("vanished_entities"):
        v = ", ".join(
            f"{e['name']} (chỉ {e['n_chapters']} chương, cuối ở ch.{e['last_ch']:g})"
            for e in stats["vanished_entities"]
        )
        lines.append(f"- Nhân vật xuất hiện ít rồi biến mất: {v}.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- gọi LLM

def _ask(prompt: str, timeout: int | None = None) -> str:
    cfg = get_ollama()
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_REVIEW},
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
        timeout=timeout or cfg.timeout,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _parse(raw: str) -> dict:
    """Đọc JSON, chịu được bị cắt giữa chừng (conflict.py cùng vấn đề)."""
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            d = json.loads(m.group())
            return {
                "summary": str(d.get("summary", ""))[:1500],
                "strengths": d.get("strengths") or [],
                "issues": d.get("issues") or [],
                "score": d.get("score") or {},
                "truncated": False,
            }
        except json.JSONDecodeError:
            pass

    # JSON hỏng — vẫn trả phần đọc được thay vì vứt hết
    m2 = re.search(r'"summary"\s*:\s*"([^"]{0,1500})', raw)
    return {
        "summary": m2.group(1) if m2 else raw[:1000],
        "strengths": [],
        "issues": [],
        "score": {},
        "truncated": True,
        "raw": raw[:3000],
    }


# ---------------------------------------------------------------- đầu vào

def review_chapter(chapter: float, comic_id: int, aspects: list[str] | None = None) -> dict:
    """Đánh giá một chương."""
    if not get_ollama().configured:
        return {"available": False, "error": "Chưa cấu hình Ollama (trang Cài đặt hoặc .env)."}

    driver = get_retriever()._get_driver()
    if driver is None:
        return {"available": False, "error": "Chưa kết nối được Neo4j."}

    picked = [a for a in (aspects or list(ASPECTS)) if a in ASPECTS]
    if not picked:
        picked = list(ASPECTS)

    try:
        with driver.session() as s:
            chunks = s.run(Q_ONE_CHAPTER, cid=comic_id, ch=float(chapter)).data()
            if not chunks:
                return {
                    "available": False,
                    "error": f"Chương {chapter:g} chưa có trong đồ thị — nạp truyện trước.",
                }
            ents = s.run(Q_CHAPTER_ENTITIES, cid=comic_id, ch=float(chapter)).data()
            scenes = s.run(Q_CHAPTER_SCENES, cid=comic_id, ch=float(chapter)).data()
            stats = _collect_stats(s, comic_id)
    except Exception as e:
        logger.exception("Đọc chương để đánh giá hỏng")
        return {"available": False, "error": str(e)}

    # Chương dài có thể vượt context — cắt phần giữa, giữ đầu và cuối
    text = "\n\n".join(c["text"] for c in chunks)
    if len(text) > 11000:
        text = text[:7000] + "\n\n[… lược phần giữa …]\n\n" + text[-3500:]

    ctx = [_format_stats(stats)]
    if ents:
        names = ", ".join(
            f"{e['name']}" + (" (lần đầu xuất hiện ở đây)" if e["first_ch"] == chapter else "")
            for e in ents
        )
        ctx.append(f"NHÂN VẬT CÓ MẶT Ở CHƯƠNG NÀY: {names}.\n")
    if scenes:
        sc = "\n".join(
            f"  {i+1}. {s['summary']}"
            + (f" (không khí: {', '.join(s['moods'])})" if s.get("moods") else "")
            for i, s in enumerate(scenes)
        )
        ctx.append(f"CÁC CẢNH TRONG CHƯƠNG (trích tự động):\n{sc}\n")

    guide = "\n".join(f"- {ASPECTS[a]['label']}: {ASPECTS[a]['guide']}" for a in picked)
    prompt = (
        f"{''.join(ctx)}\n"
        f"NỘI DUNG CHƯƠNG {chapter:g}:\n\n{text}\n\n"
        f"---\nHãy đánh giá chương {chapter:g} theo các khía cạnh:\n{guide}\n\n"
        "Nhớ: mỗi nhận xét phải kèm dẫn chứng cụ thể."
    )

    try:
        result = _parse(_ask(prompt))
    except Exception as e:
        logger.exception("Đánh giá chương hỏng")
        return {"available": False, "error": str(e)}

    return {
        "available": True,
        "scope": "chapter",
        "chapter": chapter,
        "aspects": picked,
        "n_chunks": len(chunks),
        "chars": len(text),
        **result,
    }


def review_story(comic_id: int, aspects: list[str] | None = None) -> dict:
    """Đánh giá toàn truyện — dựa trên số liệu và tóm tắt cảnh, không đọc hết văn bản."""
    if not get_ollama().configured:
        return {"available": False, "error": "Chưa cấu hình Ollama (trang Cài đặt hoặc .env)."}

    driver = get_retriever()._get_driver()
    if driver is None:
        return {"available": False, "error": "Chưa kết nối được Neo4j."}

    picked = [a for a in (aspects or list(ASPECTS)) if a in ASPECTS]
    if not picked:
        picked = list(ASPECTS)

    try:
        with driver.session() as s:
            stats = _collect_stats(s, comic_id)
            if not stats:
                return {
                    "available": False,
                    "error": "Chưa có chương nào trong đồ thị — nạp truyện trước.",
                }
            # Tóm tắt cảnh theo chương để LLM nắm mạch truyện mà không cần đọc hết
            scenes = s.run(
                """
                MATCH (c:Chapter {comic_id: $cid})-[:HAS_SCENE]->(sc:Scene)
                RETURN c.number AS ch, sc.summary AS summary, sc.order AS ord
                ORDER BY c.number, sc.order
                """,
                cid=comic_id,
            ).data()
    except Exception as e:
        logger.exception("Đọc truyện để đánh giá hỏng")
        return {"available": False, "error": str(e)}

    outline = ""
    if scenes:
        by_ch: dict[float, list[str]] = {}
        for sc in scenes:
            by_ch.setdefault(sc["ch"], []).append(sc["summary"])
        lines = [
            f"ch.{ch:g}: " + " / ".join(v[:3])
            for ch, v in sorted(by_ch.items())
        ]
        outline = "MẠCH TRUYỆN (tóm tắt cảnh từng chương):\n" + "\n".join(lines) + "\n\n"
        if len(outline) > 9000:
            outline = outline[:9000] + "\n[… lược phần còn lại …]\n\n"
    else:
        outline = (
            "(Chưa trích cảnh — chưa có mạch truyện chi tiết. "
            "Đánh giá dựa trên số liệu và cấu trúc chương.)\n\n"
        )

    guide = "\n".join(f"- {ASPECTS[a]['label']}: {ASPECTS[a]['guide']}" for a in picked)
    prompt = (
        f"{_format_stats(stats)}\n{outline}"
        f"---\nHãy đánh giá TOÀN BỘ truyện theo các khía cạnh:\n{guide}\n\n"
        "Nhớ: mỗi nhận xét phải kèm dẫn chứng [ch.N] cụ thể."
    )

    try:
        result = _parse(_ask(prompt, timeout=max(get_ollama().timeout, 300)))
    except Exception as e:
        logger.exception("Đánh giá truyện hỏng")
        return {"available": False, "error": str(e)}

    return {
        "available": True,
        "scope": "story",
        "aspects": picked,
        "stats": {
            "n_chapters": stats["n_chapters"],
            "total_chars": stats["total_chars"],
            "avg_chars": stats["avg_chars"],
            "outliers_long": stats["outliers_long"],
            "outliers_short": stats["outliers_short"],
        },
        "had_scenes": bool(scenes),
        **result,
    }
