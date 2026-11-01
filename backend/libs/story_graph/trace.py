"""Ghi lại quá trình suy luận của chat — để người viết kiểm chứng được.

Vì sao cần: câu trả lời có thể đúng vì lý do sai (research/notes/03 — hệ thống
trả lời "không tìm thấy" vì mù, không phải vì hiểu). Không nhìn được quá trình
thì không phân biệt được hai thứ đó.

Mỗi phiên truy hồi ghi:
  - định tuyến: chọn route nào, vì sao
  - từng truy vấn Cypher: câu lệnh, tham số, số kết quả, mẫu kết quả
  - prompt cuối gửi cho LLM
  - câu trả lời

Trace lưu trong bộ nhớ, giới hạn số phiên gần nhất. Không ghi DB vì đây là
công cụ chẩn đoán, không phải dữ liệu nghiệp vụ.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

MAX_TRACES = 50          # giữ 50 phiên gần nhất
MAX_SAMPLE_CHARS = 400   # cắt mẫu kết quả cho gọn


@dataclass
class QueryStep:
    """Một truy vấn Cypher hoặc một phép tính trong quá trình truy hồi."""

    label: str
    kind: str                      # cypher | embed | decision | llm
    cypher: str | None = None
    params: dict = field(default_factory=dict)
    n_results: int | None = None
    sample: list[str] = field(default_factory=list)
    note: str | None = None
    ms: float | None = None

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "kind": self.kind,
            "cypher": self.cypher,
            "params": self.params,
            "n_results": self.n_results,
            "sample": self.sample,
            "note": self.note,
            "ms": round(self.ms, 1) if self.ms is not None else None,
        }


@dataclass
class Trace:
    id: str
    question: str
    comic_id: int
    chapter: float | None = None
    route: str | None = None
    steps: list[QueryStep] = field(default_factory=list)
    prompt: str | None = None
    answer: str | None = None
    created_at: float = field(default_factory=time.time)
    total_ms: float | None = None

    def as_dict(self, full: bool = False) -> dict:
        d = {
            "id": self.id,
            "question": self.question,
            "comic_id": self.comic_id,
            "chapter": self.chapter,
            "route": self.route,
            "n_steps": len(self.steps),
            "created_at": self.created_at,
            "total_ms": round(self.total_ms, 1) if self.total_ms else None,
        }
        if full:
            d["steps"] = [s.as_dict() for s in self.steps]
            d["prompt"] = self.prompt
            d["answer"] = self.answer
        return d


class TraceRecorder:
    """Ghi các bước của MỘT phiên truy hồi.

    Dùng như context manager để tự tính thời gian, và tự lưu vào store khi xong.
    """

    def __init__(self, question: str, comic_id: int, chapter: float | None):
        self.trace = Trace(
            id=uuid.uuid4().hex[:12],
            question=question,
            comic_id=comic_id,
            chapter=chapter,
        )
        self._t0 = time.perf_counter()

    def decision(self, label: str, note: str) -> None:
        self.trace.steps.append(QueryStep(label=label, kind="decision", note=note))

    def set_route(self, route: str) -> None:
        self.trace.route = route

    def step(self, label: str, kind: str = "cypher", **kw) -> "_StepTimer":
        return _StepTimer(self, label, kind, kw)

    def record(
        self,
        label: str,
        kind: str,
        cypher: str | None = None,
        params: dict | None = None,
        results: list | None = None,
        note: str | None = None,
        ms: float | None = None,
    ) -> None:
        sample = []
        if results:
            for r in results[:3]:
                if isinstance(r, dict):
                    txt = (
                        r.get("text")
                        or r.get("summary")
                        or r.get("name")
                        or r.get("detail")
                        or str(r)
                    )
                    ch = r.get("chapter")
                    prefix = f"[ch.{ch:g}] " if isinstance(ch, (int, float)) else ""
                    sample.append(f"{prefix}{str(txt)[:MAX_SAMPLE_CHARS]}")
                else:
                    sample.append(str(r)[:MAX_SAMPLE_CHARS])

        self.trace.steps.append(
            QueryStep(
                label=label,
                kind=kind,
                cypher=_tidy_cypher(cypher),
                params=_safe_params(params or {}),
                n_results=len(results) if results is not None else None,
                sample=sample,
                note=note,
                ms=ms,
            )
        )

    def finish(self, prompt: str | None = None, answer: str | None = None) -> Trace:
        self.trace.prompt = prompt
        self.trace.answer = answer
        self.trace.total_ms = (time.perf_counter() - self._t0) * 1000
        _store.put(self.trace)
        return self.trace


class _StepTimer:
    """`with rec.step("tìm chunk") as st: ... st.done(rows)`"""

    def __init__(self, rec: TraceRecorder, label: str, kind: str, kw: dict):
        self.rec = rec
        self.label = label
        self.kind = kind
        self.kw = kw
        self._t0 = time.perf_counter()

    def __enter__(self) -> "_StepTimer":
        return self

    def __exit__(self, *exc) -> None:
        if not getattr(self, "_done", False):
            self.done(None, note="(không có kết quả)")

    def done(self, results: list | None, note: str | None = None) -> None:
        self._done = True
        self.rec.record(
            label=self.label,
            kind=self.kind,
            results=results,
            note=note or self.kw.get("note"),
            cypher=self.kw.get("cypher"),
            params=self.kw.get("params"),
            ms=(time.perf_counter() - self._t0) * 1000,
        )


def _tidy_cypher(q: str | None) -> str | None:
    """Bỏ thụt lề thừa cho dễ đọc trên UI."""
    if not q:
        return None
    lines = [ln.rstrip() for ln in q.strip().splitlines()]
    if not lines:
        return None
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    cut = min(indents) if indents else 0
    return "\n".join(ln[cut:] if len(ln) >= cut else ln for ln in lines)


def _safe_params(params: dict) -> dict:
    """Vector 1024 chiều không hiển thị được — thay bằng mô tả."""
    out = {}
    for k, v in params.items():
        if isinstance(v, list) and len(v) > 20 and all(isinstance(x, float) for x in v[:5]):
            out[k] = f"<vector {len(v)} chiều>"
        elif isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + "…"
        else:
            out[k] = v
    return out


class _TraceStore:
    """Lưu trace gần nhất trong bộ nhớ, cũ nhất bị đẩy ra."""

    def __init__(self, maxsize: int = MAX_TRACES):
        self._data: OrderedDict[str, Trace] = OrderedDict()
        self._lock = threading.Lock()
        self._maxsize = maxsize

    def put(self, trace: Trace) -> None:
        with self._lock:
            self._data[trace.id] = trace
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def get(self, trace_id: str) -> Trace | None:
        with self._lock:
            return self._data.get(trace_id)

    def list(self, comic_id: int | None = None, limit: int = 20) -> list[dict]:
        with self._lock:
            traces = list(self._data.values())
        traces.reverse()
        if comic_id is not None:
            traces = [t for t in traces if t.comic_id == comic_id]
        return [t.as_dict() for t in traces[:limit]]


_store = _TraceStore()


def get_trace(trace_id: str) -> dict | None:
    t = _store.get(trace_id)
    return t.as_dict(full=True) if t else None


def list_traces(comic_id: int | None = None, limit: int = 20) -> list[dict]:
    return _store.list(comic_id, limit)
