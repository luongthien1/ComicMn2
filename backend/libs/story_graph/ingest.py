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
from core.config import settings

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
    out: list[list[float]] = []
    with httpx.Client(timeout=300) as client:
        for i in range(0, len(texts), EMBED_BATCH):
            batch = texts[i:i + EMBED_BATCH]
            r = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={"model": settings.EMBED_MODEL, "input": batch},
                headers={"Authorization": f"Bearer {settings.OLLAMA_TOKEN}"},
            )
            r.raise_for_status()
            for vec in r.json()["embeddings"]:
                norm = sum(v * v for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
    return out


# ---------------------------------------------------------------- ghi graph

SCHEMA = [
    "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (c:Chapter) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT fine_id IF NOT EXISTS FOR (f:FineChunk) REQUIRE f.id IS UNIQUE",
    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.comic_id, e.name)",
    "CREATE INDEX fact_kind IF NOT EXISTS FOR (f:Fact) ON (f.kind)",
]

VECTOR_INDEX = """
CREATE VECTOR INDEX %s IF NOT EXISTS
FOR (n:%s) ON n.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: $dim,
  `vector.similarity_function`: 'cosine'
}}
"""


def _write_chapter(session, comic_id: int, ch: dict, coarse, fine, dim: int) -> None:
    cid = f"{comic_id}-{ch['number']:g}"
    session.run(
        """
        MERGE (c:Chapter {id: $id})
        SET c.comic_id = $comic_id, c.number = $number, c.title = $title
        """,
        id=cid, comic_id=comic_id, number=ch["number"], title=ch.get("title") or "",
    )

    if coarse:
        session.run(
            """
            UNWIND $rows AS r
            MERGE (ck:Chunk {id: r.id})
            SET ck.text = r.text, ck.offset = r.offset,
                ck.chapter = r.chapter, ck.embedding = r.embedding
            WITH ck, r
            MATCH (c:Chapter {id: r.chapter_id})
            MERGE (c)-[:HAS_CHUNK]->(ck)
            """,
            rows=coarse,
        )
    if fine:
        session.run(
            """
            UNWIND $rows AS r
            MERGE (f:FineChunk {id: r.id})
            SET f.text = r.text, f.offset = r.offset,
                f.chapter = r.chapter, f.embedding = r.embedding
            WITH f, r
            MATCH (c:Chapter {id: r.chapter_id})
            MERGE (c)-[:HAS_FINE]->(f)
            """,
            rows=fine,
        )


def _rebuild_entities(session, comic_id: int, chapters: list[dict]) -> int:
    """Timeline thực thể — quét cơ học, KHÔNG dùng LLM.

    Đếm chuỗi là việc máy làm chính xác 100%; dùng LLM ở đây chỉ thêm chỗ để sai
    (research/notes/05).
    """
    names = _candidate_names(chapters)
    rows = []
    for name in names:
        pat = re.compile(rf"\b{re.escape(name)}\b")
        chs = [c["number"] for c in chapters if pat.search(c["text"])]
        if len(chs) >= 2:
            rows.append({
                "name": name, "first_ch": min(chs), "last_ch": max(chs),
                "n_chapters": len(chs), "chapters": chs,
            })

    if not rows:
        return 0

    session.run(
        """
        UNWIND $rows AS r
        MERGE (e:Entity {comic_id: $cid, name: r.name})
        SET e.first_ch = r.first_ch, e.last_ch = r.last_ch, e.n_chapters = r.n_chapters
        MERGE (f:Fact {comic_id: $cid, kind: 'EXISTS', subject: r.name})
        SET f.from_ch = r.first_ch, f.to_ch = null, f.confidence = 'high',
            f.source = 'quét cơ học tên riêng trên toàn bộ chương'
        MERGE (f)-[:ABOUT]->(e)
        """,
        rows=rows, cid=comic_id,
    )
    links = [
        {"name": r["name"], "chapter_id": f"{comic_id}-{c:g}"}
        for r in rows for c in r["chapters"]
    ]
    session.run(
        """
        UNWIND $rows AS r
        MATCH (e:Entity {comic_id: $cid, name: r.name})
        MATCH (c:Chapter {id: r.chapter_id})
        MERGE (e)-[:APPEARS_IN]->(c)
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


# ---------------------------------------------------------------- chạy

def run_ingest(comic_id: int, chapters: list[dict]) -> dict:
    """chapters: [{number, title, text}] — text đã bỏ HTML."""
    from neo4j import GraphDatabase

    prog = IngestProgress(running=True, stage="chuẩn bị", total=len(chapters))
    with _lock:
        _progress[comic_id] = prog

    driver = None
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        dim = len(embed_batch(["kiểm tra kích thước vector"])[0])

        with driver.session() as s:
            for stmt in SCHEMA:
                s.run(stmt)
            s.run(VECTOR_INDEX % ("chunk_embedding", "Chunk"), dim=dim)
            s.run(VECTOR_INDEX % ("fine_embedding", "FineChunk"), dim=dim)

            for i, ch in enumerate(chapters, 1):
                prog.stage = f"chương {ch['number']:g}"
                prog.done = i - 1

                coarse_parts = chunk_text(ch["text"])
                fine_parts = split_sentences(ch["text"])
                texts = [t for _, t in coarse_parts] + [t for _, t in fine_parts]
                if not texts:
                    continue

                vecs = embed_batch(texts)
                n_coarse = len(coarse_parts)
                coarse = [
                    {
                        "id": f"{comic_id}-c{ch['number']:g}-{j}",
                        "chapter_id": f"{comic_id}-{ch['number']:g}",
                        "chapter": ch["number"], "offset": off,
                        "text": txt, "embedding": vecs[j],
                    }
                    for j, (off, txt) in enumerate(coarse_parts)
                ]
                fine = [
                    {
                        "id": f"{comic_id}-f{ch['number']:g}-{j}",
                        "chapter_id": f"{comic_id}-{ch['number']:g}",
                        "chapter": ch["number"], "offset": off,
                        "text": txt, "embedding": vecs[n_coarse + j],
                    }
                    for j, (off, txt) in enumerate(fine_parts)
                ]
                _write_chapter(s, comic_id, ch, coarse, fine, dim)
                prog.done = i

            prog.stage = "dựng thực thể"
            n_ent = _rebuild_entities(s, comic_id, chapters)

            row = s.run(
                """
                MATCH (c:Chapter {comic_id: $cid}) WITH count(c) AS chapters
                MATCH (ck:Chunk) WITH chapters, count(ck) AS chunks
                MATCH (e:Entity {comic_id: $cid})
                RETURN chapters, chunks, count(e) AS entities
                """,
                cid=comic_id,
            ).single()
            prog.stats = {**dict(row), "entities_rebuilt": n_ent}

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
