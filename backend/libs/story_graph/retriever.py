"""Truy hồi ngữ cảnh truyện từ Neo4j.

Xem docstring của package để biết căn cứ số liệu cho từng lựa chọn.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache

import httpx
from core.config import settings

logger = logging.getLogger(__name__)

# Câu hỏi về cảnh/mô tả — Scene graph trả lời tốt hơn (research/notes/13)
SCENE_HINT = re.compile(
    r"cảnh nào|đoạn nào|mô tả|miêu tả|không khí|bối cảnh|tả cảnh|"
    r"thời tiết|bóng tối|ánh sáng|mùi|tiếng|cảm giác",
    re.I,
)

# Câu hỏi vượt khỏi một chương dù người dùng đang mở chương nào
CROSS_CHAPTER = re.compile(
    r"từ đầu|toàn bộ|cả truyện|lần đầu|lần cuối|mâu thuẫn|trước đó|"
    r"các chương|những chương|xuyên suốt|tổng cộng|bao nhiêu lần|bao nhiêu chương",
    re.I,
)

# Câu tìm CHI TIẾT cụ thể — chunk nhỏ giúp.
# Câu định nghĩa/gộp — chunk nhỏ làm loãng ngữ cảnh và HẠI (research/notes/14 vòng 9).
DETAIL_HINT = re.compile(
    r"cảnh nào|đoạn nào|có .{0,12}(?:nào|không)\?|ở đâu|lúc nào|"
    r"mùi|tiếng|nôn|máu|khóc|cười|đau|thương|chạy|bay|lơ lửng",
    re.I,
)
BROAD_HINT = re.compile(
    r"là (?:ai|gì|những gì)|gồm những|thay đổi thế nào|bao nhiêu|"
    r"quan hệ gì|vì sao|tại sao|khác .{0,15}thế nào",
    re.I,
)


def _explain_route(
    question: str, chapter: float | None, route: str, target: float | None
) -> str:
    """Giải thích vì sao chọn route này — hiển thị trong trace."""
    m = re.search(r"chương\s+(\d+(?:\.\d+)?)", question, re.I)
    if route == "scene":
        kw = SCENE_HINT.search(question)
        return (
            f"Câu hỏi chứa '{kw.group()}' → hỏi về cảnh/mô tả. "
            "Dùng Scene graph + vector, không giới hạn chương."
        )
    if route == "chapter" and m:
        return (
            f"Câu hỏi nêu rõ 'chương {m.group(1)}' → giới hạn truy hồi trong chương đó. "
            "Đo được: giới hạn phạm vi nâng 3/7 lên 7/7 (research/notes/09)."
        )
    if route == "chapter":
        return (
            f"Đang mở chương {target:g} và câu hỏi không có từ khoá xuyên chương "
            "→ giới hạn trong chương đang mở."
        )
    if chapter is not None:
        kw = CROSS_CHAPTER.search(question)
        return (
            f"Đang mở chương {chapter:g} nhưng câu hỏi chứa "
            f"'{kw.group() if kw else '—'}' → mở rộng ra toàn truyện."
        )
    return "Không có chương cụ thể → tìm trên toàn truyện."


@dataclass
class StoryContext:
    """Ngữ cảnh truy hồi được, sẵn sàng ghép vào prompt."""

    chunks: list[dict] = field(default_factory=list)
    scenes: list[dict] = field(default_factory=list)
    facts: str = ""
    route: str = "global"
    chapter: float | None = None
    available: bool = True
    error: str | None = None

    def to_prompt_block(self) -> str:
        """Dựng phần tư liệu để chèn vào prompt. Rỗng nếu không có gì."""
        if not (self.facts or self.scenes or self.chunks):
            return ""

        parts = []
        if self.facts:
            parts.append(self.facts)

        if self.scenes:
            lines = []
            for h in self.scenes:
                bits = [f"[ch.{h['chapter']:g}] {h.get('summary') or ''}"]
                if h.get("key_action"):
                    bits.append(f"hành động: {h['key_action']}")
                if h.get("physical_state"):
                    bits.append(f"trạng thái: {h['physical_state']}")
                if h.get("sensory"):
                    bits.append(f"giác quan: {', '.join(h['sensory'])}")
                lines.append("- " + " | ".join(bits))
            parts.append("CÁC CẢNH TỪ ĐỒ THỊ:\n" + "\n".join(lines) + "\n")

        if self.chunks:
            head = (
                f"ĐOẠN TRÍCH (chỉ chương {self.chapter:g}):"
                if self.chapter is not None
                else "ĐOẠN TRÍCH TỪ TRUYỆN:"
            )
            body = "\n\n".join(
                f"[ch.{c['chapter']:g}] {c['text']}" for c in self.chunks
            )
            parts.append(f"{head}\n\n{body}\n")

        return "\n".join(parts) + "\n"

    @property
    def chapters_used(self) -> list[float]:
        return sorted(
            {c["chapter"] for c in self.chunks} | {s["chapter"] for s in self.scenes}
        )


class StoryRetriever:
    def __init__(self):
        self._driver = None

    # ------------------------------------------------------------ kết nối

    def _get_driver(self):
        """Kết nối lười. Trả None nếu không dùng được — chat vẫn phải chạy."""
        if self._driver is not None:
            return self._driver
        if not settings.NEO4J_URI:
            return None
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_timeout=5,
            )
            driver.verify_connectivity()
            self._driver = driver
            return driver
        except Exception as e:
            logger.warning("Không kết nối được Neo4j (%s): %s", settings.NEO4J_URI, e)
            return None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def _embed(self, text: str) -> list[float] | None:
        """Nhúng câu hỏi qua ollama. None nếu hỏng — vẫn còn graph facts."""
        if not settings.OLLAMA_TOKEN:
            return None
        try:
            r = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={"model": settings.EMBED_MODEL, "input": [text]},
                headers={"Authorization": f"Bearer {settings.OLLAMA_TOKEN}"},
                timeout=30,
            )
            r.raise_for_status()
            vec = r.json()["embeddings"][0]
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            return [v / norm for v in vec]
        except Exception as e:
            logger.warning("Embed hỏng: %s", e)
            return None

    # ------------------------------------------------------------ định tuyến

    @staticmethod
    def wants_detail(question: str) -> bool:
        """Câu này có nên thêm chunk nhỏ không?

        Khi cả hai mẫu cùng khớp, ưu tiên BROAD: loãng ngữ cảnh hại nhiều loại
        câu hơn là thiếu chi tiết hại một loại (research/notes/14 vòng 9).
        """
        if BROAD_HINT.search(question):
            return False
        return bool(DETAIL_HINT.search(question))

    @staticmethod
    def decide_route(question: str, chapter: float | None) -> tuple[str, float | None]:
        m = re.search(r"chương\s+(\d+(?:\.\d+)?)", question, re.I)
        explicit = float(m.group(1)) if m else None

        if SCENE_HINT.search(question) and explicit is None:
            return "scene", None
        if explicit is not None:
            return "chapter", explicit
        if chapter is not None and not CROSS_CHAPTER.search(question):
            return "chapter", chapter
        return "global", None

    # ------------------------------------------------------------ truy vấn

    def _run(self, s, rec, label, cypher, **params):
        """Chạy Cypher và ghi trace nếu có recorder."""
        if rec is None:
            return s.run(cypher, **params).data()
        with rec.step(label, "cypher", cypher=cypher, params=params) as st:
            rows = s.run(cypher, **params).data()
            st.done(rows)
            return rows

    Q_VEC_GLOBAL = """
        CALL db.index.vector.queryNodes('chunk_embedding', $k, $vec)
        YIELD node, score
        RETURN node.chapter AS chapter, node.text AS text, score
    """

    Q_VEC_FINE = """
        CALL db.index.vector.queryNodes('fine_embedding', $k, $vec)
        YIELD node, score
        RETURN node.chapter AS chapter, node.text AS text, score
    """

    # Index vector không lọc trực tiếp được; lấy sâu 300 rồi lọc theo chương.
    Q_VEC_CHAPTER = """
        CALL db.index.vector.queryNodes('chunk_embedding', 300, $vec)
        YIELD node, score
        WHERE node.chapter = $ch
        RETURN node.chapter AS chapter, node.text AS text, score
        ORDER BY score DESC LIMIT $k
    """

    Q_CHAPTER_HEAD = """
        MATCH (c:Chapter {number: $ch})-[:HAS_CHUNK]->(ck:Chunk)
        RETURN ck.chapter AS chapter, ck.text AS text, 0.0 AS score
        ORDER BY ck.offset LIMIT $k
    """

    Q_VEC_IN_CHAPTERS = """
        CALL db.index.vector.queryNodes('chunk_embedding', 300, $vec)
        YIELD node, score
        WHERE node.chapter IN $chapters
        RETURN node.chapter AS chapter, node.text AS text, score
        ORDER BY score DESC LIMIT $k
    """

    Q_SCENES = """
        CALL db.index.fulltext.queryNodes('scene_text', $q)
        YIELD node, score
        RETURN node.chapter AS chapter, node.summary AS summary,
               node.key_action AS key_action,
               node.physical_state AS physical_state,
               node.sensory AS sensory, score
        ORDER BY score DESC LIMIT $k
    """

    def _vec_global(self, s, qv, k, rec=None):
        return self._run(s, rec, "vector toàn truyện (chunk lớn)",
                         self.Q_VEC_GLOBAL, k=k, vec=qv)

    def _vec_fine(self, s, qv, k, rec=None):
        try:
            return self._run(s, rec, "vector chunk nhỏ (~96 ký tự)",
                             self.Q_VEC_FINE, k=k, vec=qv)
        except Exception as e:
            if rec:
                rec.decision("chunk nhỏ", f"Không dùng được (chưa nạp?): {e}")
            return []

    def _vec_chapter(self, s, qv, ch, k, rec=None):
        rows = self._run(s, rec, f"vector giới hạn trong chương {ch:g}",
                         self.Q_VEC_CHAPTER, vec=qv, ch=ch, k=k)
        if rows:
            return rows
        if rec:
            rec.decision(
                "dự phòng",
                f"Không đoạn nào trong chương {ch:g} khớp câu hỏi → lấy phần đầu chương.",
            )
        return self._run(s, rec, f"phần đầu chương {ch:g}",
                         self.Q_CHAPTER_HEAD, ch=ch, k=k)

    def _vec_in_chapters(self, s, qv, chapters, k, rec=None):
        if not chapters:
            return []
        return self._run(s, rec, "vector trong các chương Scene gợi ý",
                         self.Q_VEC_IN_CHAPTERS, vec=qv, chapters=chapters, k=k)

    def _scenes(self, s, question, k=6, rec=None):
        terms = [t for t in re.findall(r"\w+", question) if len(t) > 2]
        if not terms:
            return []
        try:
            return self._run(s, rec, "full-text trên mô tả cảnh",
                             self.Q_SCENES, q=" OR ".join(terms), k=k)
        except Exception as e:
            if rec:
                rec.decision("scene", f"Không tìm được cảnh (chưa nạp Scene?): {e}")
            return []

    Q_ENTITIES = """
        MATCH (e:Entity {comic_id: $cid})
        WHERE toLower($q) CONTAINS toLower(e.name)
           OR any(a IN coalesce(e.aliases, []) WHERE toLower($q) CONTAINS toLower(a))
        RETURN e.name AS name, e.first_ch AS first_ch, e.last_ch AS last_ch,
               e.description AS description
        ORDER BY e.first_ch
    """

    Q_NEGATIVE_FACTS = """
        MATCH (f:Fact {comic_id: $cid})
        WHERE f.statement IS NOT NULL
          AND any(t IN f.triggers WHERE toLower($q) CONTAINS toLower(t))
        RETURN f.statement AS statement, f.evidence_ch AS ch
    """

    Q_RELATIONS = """
        MATCH (f:Fact {comic_id: $cid})-[:ABOUT]->(e:Entity)
        WHERE e.name IN $names AND f.detail IS NOT NULL AND f.detail <> ''
        RETURN DISTINCT f.detail AS detail, f.from_ch AS ch, f.kind AS kind ORDER BY ch
    """

    Q_PRESENT_IN_CHAPTER = """
        MATCH (e:Entity {comic_id: $cid})-[:APPEARS_IN]->(c:Chapter {number: $ch})
        RETURN e.name AS name ORDER BY e.name
    """

    def _facts(self, s, question, chapter, comic_id, rec=None):
        """Sự thật cơ học từ graph — phần giải được câu hỏi thời gian."""
        lines = []

        ents = self._run(s, rec, "tìm thực thể được nhắc trong câu hỏi",
                         self.Q_ENTITIES, cid=comic_id, q=question)
        for e in ents:
            if e["description"]:
                lines.append(f"- {e['name']}: {e['description']}")
            elif e["first_ch"] is not None:
                # Nêu rõ "từ ... trở đi" thay vì "từ ... đến ...".
                # Model từng hiểu "xuất hiện ch.21" thành "chỉ có ở ch.21" rồi báo
                # mâu thuẫn cho đoạn đặt ở ch.22 (research/notes/16).
                lines.append(
                    f"- '{e['name']}' xuất hiện LẦN ĐẦU ở chương {e['first_ch']:g}, "
                    f"lần cuối ở chương {e['last_ch']:g} — nghĩa là hợp lệ ở mọi "
                    f"chương từ {e['first_ch']:g} trở đi."
                )

        negs = self._run(s, rec, "tìm Fact phủ định (theo trigger)",
                         self.Q_NEGATIVE_FACTS, cid=comic_id, q=question)
        for n in negs:
            lines.append(f"- QUAN TRỌNG: {n['statement']} (xem [ch.{n['ch']:g}])")

        if ents:
            rels = self._run(s, rec, "tìm quan hệ có nghĩa của các thực thể đó",
                             self.Q_RELATIONS, cid=comic_id,
                             names=[e["name"] for e in ents])
            for r in rels:
                lines.append(f"- {r['detail']} [ch.{r['ch']:g}]")

        if chapter is not None:
            present = self._run(s, rec, f"ai có mặt ở chương {chapter:g}",
                                self.Q_PRESENT_IN_CHAPTER, cid=comic_id, ch=chapter)
            if present:
                names = ", ".join(p["name"] for p in present)
                lines.append(f"- Chương {chapter:g} có mặt: {names}.")
            for e in ents:
                if e["first_ch"] is not None and chapter < e["first_ch"]:
                    lines.append(
                        f"- LƯU Ý: '{e['name']}' CHƯA xuất hiện tại chương "
                        f"{chapter:g} (chỉ từ chương {e['first_ch']:g} trở đi)."
                    )

        return "SỰ THẬT TỪ ĐỒ THỊ:\n" + "\n".join(lines) + "\n" if lines else ""

    # ------------------------------------------------------------ đầu vào chính

    def retrieve(
        self,
        question: str,
        chapter: float | None = None,
        comic_id: int = 1,
        k: int = 8,
        rec=None,
    ) -> StoryContext:
        """Truy hồi ngữ cảnh. Truyền `rec` (TraceRecorder) để ghi lại quá trình."""
        driver = self._get_driver()
        if driver is None:
            if rec:
                rec.decision("kết nối", "Không kết nối được Neo4j — bỏ qua tra cứu.")
            return StoryContext(
                available=False,
                error="Chưa kết nối được Neo4j — chat vẫn trả lời nhưng không tra cứu được truyện.",
            )

        route, target = self.decide_route(question, chapter)
        if rec:
            rec.set_route(route)
            rec.decision("định tuyến", _explain_route(question, chapter, route, target))

        qv = self._embed(question)
        if rec:
            rec.record(
                "nhúng câu hỏi", "embed",
                note=(
                    f"Dùng {settings.EMBED_MODEL} → vector {len(qv)} chiều"
                    if qv else "Không tạo được embedding — chỉ dùng sự thật từ đồ thị"
                ),
            )

        try:
            with driver.session() as s:
                facts = self._facts(s, question, target, comic_id, rec)

                if qv is None:
                    return StoryContext(facts=facts, route=route, chapter=target)

                if route == "chapter":
                    chunks = self._vec_chapter(s, qv, target, k, rec)
                    return StoryContext(chunks, [], facts, route, target)

                if route == "scene":
                    scenes = self._scenes(s, question, rec=rec)
                    chunks = self._vec_global(s, qv, 8, rec)
                    seen = {(c["chapter"], c["text"][:60]) for c in chunks}

                    if self.wants_detail(question):
                        added = 0
                        for fine in self._vec_fine(s, qv, 5, rec):
                            key = (fine["chapter"], fine["text"][:60])
                            if key not in seen:
                                chunks.append(fine)
                                seen.add(key)
                                added += 1
                        if rec:
                            rec.decision(
                                "thêm chunk nhỏ",
                                f"Câu hỏi tìm chi tiết cụ thể → thêm {added} đoạn ngắn "
                                "(chunk lớn làm loãng tín hiệu một câu).",
                            )
                    elif rec:
                        rec.decision(
                            "bỏ qua chunk nhỏ",
                            "Câu hỏi dạng định nghĩa/gộp → chunk vụn làm loãng ngữ cảnh.",
                        )

                    if scenes:
                        cand = list({sc["chapter"] for sc in scenes})
                        added = 0
                        for extra in self._vec_in_chapters(s, qv, cand, 3, rec):
                            key = (extra["chapter"], extra["text"][:60])
                            if key not in seen:
                                chunks.append(extra)
                                seen.add(key)
                                added += 1
                        if rec:
                            rec.decision(
                                "bổ sung theo cảnh",
                                f"Scene gợi ý chương {sorted(cand)} → thêm {added} đoạn. "
                                "Scene BỔ SUNG chứ không chặn vector toàn truyện.",
                            )
                    return StoryContext(chunks, scenes, facts, route, None)

                chunks = self._vec_global(s, qv, k, rec)
                if self.wants_detail(question):
                    seen = {(c["chapter"], c["text"][:60]) for c in chunks}
                    added = 0
                    for fine in self._vec_fine(s, qv, 4, rec):
                        key = (fine["chapter"], fine["text"][:60])
                        if key not in seen:
                            chunks.append(fine)
                            seen.add(key)
                            added += 1
                    if rec:
                        rec.decision("thêm chunk nhỏ", f"Thêm {added} đoạn ngắn.")
                return StoryContext(chunks, [], facts, route, None)

        except Exception as e:
            logger.exception("Truy hồi hỏng")
            if rec:
                rec.decision("lỗi", str(e))
            return StoryContext(available=False, error=str(e))

    def stats(self, comic_id: int = 1) -> dict:
        """Thống kê graph — để UI biết đã ingest gì."""
        driver = self._get_driver()
        if driver is None:
            return {"available": False}
        try:
            with driver.session() as s:
                row = s.run(
                    """
                    OPTIONAL MATCH (c:Chapter) WITH count(c) AS chapters
                    OPTIONAL MATCH (ck:Chunk) WITH chapters, count(ck) AS chunks
                    OPTIONAL MATCH (e:Entity) WITH chapters, chunks, count(e) AS entities
                    OPTIONAL MATCH (f:Fact) WITH chapters, chunks, entities, count(f) AS facts
                    OPTIONAL MATCH (sc:Scene)
                    RETURN chapters, chunks, entities, facts, count(sc) AS scenes
                    """
                ).single()
                return {"available": True, **dict(row)}
        except Exception as e:
            return {"available": False, "error": str(e)}


@lru_cache(maxsize=1)
def get_retriever() -> StoryRetriever:
    return StoryRetriever()
