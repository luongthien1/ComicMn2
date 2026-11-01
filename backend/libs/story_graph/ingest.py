"""Nạp chương truyện vào đồ thị tri thức.

Tách khỏi research/scripts/ vì đây là đường chạy trong ứng dụng thật:
lấy chương từ database, không đọc .docx.

Ingest là việc chậm (embedding cho mỗi chunk), nên endpoint chạy nền và
API riêng để hỏi tiến độ.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field

import httpx
from core.ai_config import get_ollama
from core.config import settings

from .schema import chapter_node_id, ensure_schema

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
FINE_MIN = 60
FINE_MAX = 320
EMBED_BATCH = 16


# ---------------------------------------------------------------- tiến độ

@dataclass
class IngestProgress:
    running: bool = False
    stage: str = ""
    done: int = 0
    total: int = 0
    error: str | None = None
    finished: bool = False
    stats: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "running": self.running,
            "stage": self.stage,
            "done": self.done,
            "total": self.total,
            "percent": round(self.done / self.total * 100, 1) if self.total else 0.0,
            "error": self.error,
            "finished": self.finished,
            "stats": self.stats,
        }


_progress: dict[int, IngestProgress] = {}
_lock = threading.Lock()


def get_progress(comic_id: int) -> dict:
    with _lock:
        p = _progress.get(comic_id)
        return p.as_dict() if p else {"running": False, "finished": False, "stage": ""}


# ---------------------------------------------------------------- cắt chunk

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Cắt theo đoạn văn, gom đến khi đủ size. Trả về [(offset, chunk)]."""
    paras = [p for p in text.split("\n\n") if p.strip()]
    chunks: list[tuple[int, str]] = []
    buf: list[str] = []
    buf_len = 0
    offset = 0
    cursor = 0

    for p in paras:
        if buf_len + len(p) > size and buf:
            chunks.append((offset, "\n\n".join(buf)))
            keep: list[str] = []
            keep_len = 0
            for q in reversed(buf):
                if keep_len + len(q) > overlap:
                    break
                keep.insert(0, q)
                keep_len += len(q)
            buf = keep
            buf_len = keep_len
            offset = cursor - keep_len
        buf.append(p)
        buf_len += len(p)
        cursor += len(p) + 2

    if buf:
        chunks.append((offset, "\n\n".join(buf)))
    return chunks


def split_sentences(text: str):
    """Chunk nhỏ cắt theo câu — bắt chi tiết mà chunk lớn làm loãng."""
    out: list[tuple[int, str]] = []
    buf: list[str] = []
    buf_start = 0
    pos = 0

    for p in re.split(r"(?<=[.!?…”\"])\s+|\n+", text):
        p = p.strip()
        if not p:
            pos += 1
            continue
        start = text.find(p, pos)
        if start < 0:
            start = pos
        pos = start + len(p)

        if not buf:
            buf_start = start
        buf.append(p)
        if len(" ".join(buf)) >= FINE_MIN:
            out.append((buf_start, " ".join(buf)[:FINE_MAX]))
            buf = []

    if buf:
        out.append((buf_start, " ".join(buf)[:FINE_MAX]))
    return out


def strip_html(html: str) -> str:
    """Nội dung chương lưu dạng HTML; lấy text để embed."""
    text = re.sub(r"<br\s*/?>", "\n", html or "", flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    return re.sub(r"[ \t]+", " ", text).strip()


# ---------------------------------------------------------------- embedding

def embed_batch(texts: list[str]) -> list[list[float]]:
    cfg = get_ollama()
    out: list[list[float]] = []
    with httpx.Client(timeout=300) as client:
        for i in range(0, len(texts), EMBED_BATCH):
            batch = texts[i:i + EMBED_BATCH]
            r = client.post(
                f"{cfg.base_url}/api/embed",
                json={"model": cfg.embed_model, "input": batch},
                headers=cfg.headers,
            )
            r.raise_for_status()
            for vec in r.json()["embeddings"]:
                norm = sum(v * v for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
    return out


# ---------------------------------------------------------------- ghi graph
#
# Node do ứng dụng ghi mang `src = 'app'`. Mọi thao tác XOÁ chỉ chạm node/cạnh
# có nhãn này — dữ liệu nạp từ research/ (không có nhãn) không bị động tới.

def _embed_chapter(comic_id: int, ch: dict) -> tuple[list[dict], list[dict], int | None]:
    coarse_parts = chunk_text(ch["text"])
    fine_parts = split_sentences(ch["text"])
    texts = [t for _, t in coarse_parts] + [t for _, t in fine_parts]
    if not texts:
        return [], [], None

    vecs = embed_batch(texts)
    n_coarse = len(coarse_parts)
    num = float(ch["number"])
    chapter_id = chapter_node_id(comic_id, num)
    coarse = [
        {
            "id": f"{comic_id}-c{num:g}-{j}", "chapter_id": chapter_id,
            "chapter": num, "offset": off, "text": txt, "embedding": vecs[j],
        }
        for j, (off, txt) in enumerate(coarse_parts)
    ]
    fine = [
        {
            "id": f"{comic_id}-f{num:g}-{j}", "chapter_id": chapter_id,
            "chapter": num, "offset": off, "text": txt, "embedding": vecs[n_coarse + j],
        }
        for j, (off, txt) in enumerate(fine_parts)
    ]
    return coarse, fine, len(vecs[0])


def _write_chapter(session, comic_id: int, ch: dict, coarse: list[dict], fine: list[dict]) -> None:
    num = float(ch["number"])
    cid = chapter_node_id(comic_id, num)
    session.run(
        """
        MERGE (c:Chapter {id: $id})
        SET c.comic_id = $comic_id, c.number = $number, c.title = $title, c.src = 'app'
        """,
        id=cid, comic_id=comic_id, number=num, title=ch.get("title") or "",
    )
    # Xoá chunk cũ trước — chương ngắn đi thì chunk thừa không được treo lại.
    session.run(
        "MATCH (:Chapter {id: $id})-[:HAS_CHUNK|HAS_FINE]->(n) DETACH DELETE n",
        id=cid,
    )

    if coarse:
        session.run(
            """
            UNWIND $rows AS r
            MERGE (ck:Chunk {id: r.id})
            SET ck.text = r.text, ck.offset = r.offset, ck.comic_id = $comic_id,
                ck.chapter = r.chapter, ck.embedding = r.embedding
            WITH ck, r
            MATCH (c:Chapter {id: r.chapter_id})
            MERGE (c)-[:HAS_CHUNK]->(ck)
            """,
            rows=coarse, comic_id=comic_id,
        )
    if fine:
        session.run(
            """
            UNWIND $rows AS r
            MERGE (f:FineChunk {id: r.id})
            SET f.text = r.text, f.offset = r.offset, f.comic_id = $comic_id,
                f.chapter = r.chapter, f.embedding = r.embedding
            WITH f, r
            MATCH (c:Chapter {id: r.chapter_id})
            MERGE (c)-[:HAS_FINE]->(f)
            """,
            rows=fine, comic_id=comic_id,
        )


def _prune_chapters(session, comic_id: int, keep_numbers: list[float]) -> int:
    """Xoá chương app đã ghi nhưng không còn trong DB (bị xoá hoặc đổi số)."""
    ids = [
        r["id"] for r in session.run(
            """
            MATCH (c:Chapter {comic_id: $cid, src: 'app'})
            WHERE NOT c.number IN $keep
            RETURN c.id AS id
            """,
            cid=comic_id, keep=[float(n) for n in keep_numbers],
        )
    ]
    _prune_chapters_by_id(session, ids)
    return len(ids)


def _prune_chapters_by_id(session, ids: list[str]) -> None:
    ids = [
        r["id"] for r in session.run(
            "MATCH (c:Chapter {src: 'app'}) WHERE c.id IN $ids RETURN c.id AS id", ids=ids
        )
    ]
    if ids:
        session.run(
            """
            MATCH (c:Chapter) WHERE c.id IN $ids
            OPTIONAL MATCH (c)-[:HAS_CHUNK|HAS_FINE|HAS_SCENE]->(n)
            DETACH DELETE n
            """,
            ids=ids,
        )
        session.run("MATCH (c:Chapter) WHERE c.id IN $ids DETACH DELETE c", ids=ids)


def _rebuild_entities(session, comic_id: int, chapters: list[dict]) -> int:
    """Timeline thực thể — quét cơ học, KHÔNG dùng LLM.

    Đếm chuỗi là việc máy làm chính xác 100%; dùng LLM ở đây chỉ thêm chỗ để sai
    (research/notes/05).

    Dựng lại từ đầu mỗi lần: tên bị xoá khỏi truyện thì cạnh/Fact cũ cũng mất,
    thay vì tích tụ mãi như trước.
    """
    names = _candidate_names(chapters)
    rows = []
    for name in names:
        pat = re.compile(rf"\b{re.escape(name)}\b")
        chs = [float(c["number"]) for c in chapters if pat.search(c["text"])]
        if len(chs) >= 2:
            rows.append({
                "name": name, "first_ch": min(chs), "last_ch": max(chs),
                "n_chapters": len(chs), "chapters": chs,
            })
    keep = [r["name"] for r in rows]

    # Gỡ dữ liệu cũ do app tạo
    session.run(
        "MATCH (:Entity {comic_id: $cid})-[r:APPEARS_IN {src: 'app'}]->() DELETE r",
        cid=comic_id,
    )
    session.run(
        """
        MATCH (f:Fact {comic_id: $cid, kind: 'EXISTS', src: 'app'})
        WHERE NOT f.subject IN $keep
        DETACH DELETE f
        """,
        cid=comic_id, keep=keep,
    )
    session.run(
        """
        MATCH (e:Entity {comic_id: $cid, src: 'app'})
        WHERE NOT e.name IN $keep AND NOT ()-[:ABOUT]->(e)
        DETACH DELETE e
        """,
        cid=comic_id, keep=keep,
    )

    if not rows:
        return 0

    session.run(
        """
        UNWIND $rows AS r
        MERGE (e:Entity {comic_id: $cid, name: r.name})
        ON CREATE SET e.src = 'app'
        SET e.first_ch = r.first_ch, e.last_ch = r.last_ch, e.n_chapters = r.n_chapters
        MERGE (f:Fact {comic_id: $cid, kind: 'EXISTS', subject: r.name})
        ON CREATE SET f.src = 'app'
        SET f.from_ch = r.first_ch, f.to_ch = null, f.confidence = 'high',
            f.source = 'quét cơ học tên riêng trên toàn bộ chương'
        MERGE (f)-[:ABOUT]->(e)
        """,
        rows=rows, cid=comic_id,
    )
    links = [
        {"name": r["name"], "chapter_id": chapter_node_id(comic_id, c)}
        for r in rows for c in r["chapters"]
    ]
    session.run(
        """
        UNWIND $rows AS r
        MATCH (e:Entity {comic_id: $cid, name: r.name})
        MATCH (c:Chapter {id: r.chapter_id})
        MERGE (e)-[a:APPEARS_IN]->(c)
        ON CREATE SET a.src = 'app'
        """,
        rows=links, cid=comic_id,
    )
    return len(rows)


STOP_WORDS = {
    "Chương", "Tôi", "Nhưng", "Khi", "Không", "Đó", "Một", "Những", "Nếu",
    "Thế", "Sau", "Trong", "Cái", "Với", "Còn", "Đây", "Hắn", "Anh", "Tại",
    "Người", "Ngay", "Thật", "Chỉ", "Để", "Lúc", "Từ", "Trên", "Dưới", "Bởi",
    "Vậy", "Rồi", "Ông", "Cậu", "Chuyện", "Việc", "Ngoài", "Giờ", "Mọi",
    "Như", "Này", "Quá", "Tất", "Phải", "Theo", "Trước", "Về", "Lại", "Nhìn",
    "Nghe", "Nói", "Làm", "Thấy", "Biết", "Con", "Hai", "Cảm", "Trạng", "Hạng",
    "Được", "Đừng", "Bỗng", "Lần", "Dường", "Nhanh", "Chết", "Đúng", "Chắc",
    "Sức", "Bình", "Vẫn", "Dù", "Mà", "Điều", "Đến", "Đầu", "Thôi", "Hiện",
    "Chúng", "Thứ", "Bây", "Vật", "Cấp", "Quả", "Tuy", "Tối", "Trái", "Đất",
}


def _candidate_names(chapters: list[dict], min_count: int = 12) -> list[str]:
    from collections import Counter

    pat = re.compile(r"\b[A-ZĐ][a-zà-ỹ]{2,}\b")
    counts: Counter = Counter()
    for c in chapters:
        counts.update(pat.findall(c["text"]))
    return [
        n for n, cnt in counts.most_common(120)
        if cnt >= min_count and n not in STOP_WORDS
    ]


def _open_driver():
    from neo4j import GraphDatabase

    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        connection_timeout=10,
    )


def graph_configured() -> bool:
    return bool(settings.NEO4J_URI) and get_ollama().configured


def _comic_stats(session, comic_id: int) -> dict:
    row = session.run(
        """
        OPTIONAL MATCH (c:Chapter {comic_id: $cid}) WITH count(c) AS chapters
        OPTIONAL MATCH (ck:Chunk {comic_id: $cid}) WITH chapters, count(ck) AS chunks
        OPTIONAL MATCH (e:Entity {comic_id: $cid})
        RETURN chapters, chunks, count(e) AS entities
        """,
        cid=comic_id,
    ).single()
    return dict(row) if row else {}


# ---------------------------------------------------------------- chạy

def run_ingest(comic_id: int, chapters: list[dict]) -> dict:
    """Nạp lại toàn bộ truyện. chapters: [{number, title, text}] — text đã bỏ HTML."""
    prog = IngestProgress(running=True, stage="chuẩn bị", total=len(chapters))
    with _lock:
        _progress[comic_id] = prog

    driver = None
    try:
        driver = _open_driver()
        with driver.session() as s:
            ensure_schema(s)
            for i, ch in enumerate(chapters, 1):
                prog.stage = f"chương {float(ch['number']):g}"
                prog.done = i - 1
                coarse, fine, dim = _embed_chapter(comic_id, ch)
                if dim:
                    ensure_schema(s, dim)
                _write_chapter(s, comic_id, ch, coarse, fine)
                prog.done = i

            prog.stage = "dọn chương cũ"
            pruned = _prune_chapters(s, comic_id, [c["number"] for c in chapters])

            prog.stage = "dựng thực thể"
            n_ent = _rebuild_entities(s, comic_id, chapters)
            prog.stats = {**_comic_stats(s, comic_id), "entities_rebuilt": n_ent, "pruned": pruned}

        prog.stage = "xong"
        prog.finished = True
        return prog.stats

    except Exception as e:
        logger.exception("Ingest hỏng")
        prog.error = str(e)
        raise
    finally:
        prog.running = False
        if driver is not None:
            driver.close()


def ingest_chapter(comic_id: int, chapter: dict, all_chapters: list[dict]) -> dict:
    """Nạp lại MỘT chương sau khi lưu, rồi dựng lại timeline thực thể.

    `all_chapters` là mọi chương của truyện (cả chương ngắn) — dùng để dựng
    thực thể và dọn chương đã xoá/đổi số.
    """
    coarse, fine, dim = _embed_chapter(comic_id, chapter)
    driver = _open_driver()
    try:
        with driver.session() as s:
            ensure_schema(s, dim)
            _write_chapter(s, comic_id, chapter, coarse, fine)
            pruned = _prune_chapters(s, comic_id, [c["number"] for c in all_chapters])
            n_ent = _rebuild_entities(s, comic_id, all_chapters)
        return {
            "status": "done",
            "chapter": float(chapter["number"]),
            "chunks": len(coarse),
            "fine_chunks": len(fine),
            "entities": n_ent,
            "pruned_chapters": pruned,
        }
    finally:
        driver.close()


def delete_chapter(comic_id: int, number: float) -> None:
    """Gỡ một chương app đã ghi khỏi graph (khi xoá chương)."""
    driver = _open_driver()
    try:
        with driver.session() as s:
            _prune_chapters_by_id(s, [chapter_node_id(comic_id, number)])
    finally:
        driver.close()
