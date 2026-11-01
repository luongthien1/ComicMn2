"""Schema Neo4j dùng chung cho ingest và truy hồi.

Mọi node nội dung (Chunk, FineChunk, Scene) mang `comic_id` để truy vấn vector
lọc đúng truyện. Dữ liệu cũ (nạp trước khi có trường này, kể cả từ research/)
được gán bù từ Chapter cha — xem `backfill_comic_ids`.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SCHEMA = [
    "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (c:Chapter) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT fine_id IF NOT EXISTS FOR (f:FineChunk) REQUIRE f.id IS UNIQUE",
    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.comic_id, e.name)",
    "CREATE INDEX fact_kind IF NOT EXISTS FOR (f:Fact) ON (f.kind)",
    "CREATE INDEX chapter_comic IF NOT EXISTS FOR (c:Chapter) ON (c.comic_id, c.number)",
]

VECTOR_INDEX = """
CREATE VECTOR INDEX %s IF NOT EXISTS
FOR (n:%s) ON n.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: $dim,
  `vector.similarity_function`: 'cosine'
}}
"""

BACKFILL = """
MATCH (c:Chapter)-[:HAS_CHUNK|HAS_FINE|HAS_SCENE]->(n)
WHERE n.comic_id IS NULL AND c.comic_id IS NOT NULL
SET n.comic_id = c.comic_id
RETURN count(n) AS n
"""


def chapter_node_id(comic_id: int, number: float) -> str:
    return f"{comic_id}-{float(number):g}"


def ensure_schema(session, dim: int | None = None) -> None:
    for stmt in SCHEMA:
        session.run(stmt)
    if dim:
        session.run(VECTOR_INDEX % ("chunk_embedding", "Chunk"), dim=dim)
        session.run(VECTOR_INDEX % ("fine_embedding", "FineChunk"), dim=dim)
    backfill_comic_ids(session)


def backfill_comic_ids(session) -> int:
    try:
        n = session.run(BACKFILL).single()["n"]
        if n:
            logger.info("Đã gán bù comic_id cho %d node cũ", n)
        return n
    except Exception as e:
        logger.warning("Không gán bù được comic_id: %s", e)
        return 0
