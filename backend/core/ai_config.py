"""Cấu hình Ollama dùng chung cho mọi lời gọi AI.

Nguồn duy nhất: trang Cài đặt (bảng `ai_settings`) ghi đè, bỏ trống thì lấy `.env`.
Trước đây chat/graph đọc `.env` còn job phân tích đọc DB — hai nơi lệch nhau.

Token không lưu DB (không hiện ra UI), luôn lấy từ `.env`.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from core.config import settings

_CACHE_TTL = 15.0  # giây — tránh query DB cho từng lần embed


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    token: str
    timeout: int
    embed_model: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @property
    def configured(self) -> bool:
        return bool(self.base_url)


_lock = threading.Lock()
_cached: tuple[float, OllamaConfig] | None = None


def _load() -> OllamaConfig:
    endpoint = model = None
    try:
        from db.model.ai_settings import AiSettings
        from libs.database.connect import SessionMaker

        with SessionMaker() as db:
            row = db.get(AiSettings, 1)
            if row is not None:
                endpoint = (row.ollama_endpoint or "").strip() or None
                model = (row.ollama_model or "").strip() or None
    except Exception:
        # DB chưa sẵn sàng (test, migration chưa chạy) → dùng .env
        pass

    return OllamaConfig(
        base_url=(endpoint or settings.OLLAMA_BASE_URL).rstrip("/"),
        model=model or settings.OLLAMA_MODEL,
        token=settings.OLLAMA_TOKEN,
        timeout=settings.OLLAMA_TIMEOUT,
        embed_model=settings.EMBED_MODEL,
    )


def get_ollama() -> OllamaConfig:
    global _cached
    with _lock:
        if _cached is not None and time.monotonic() - _cached[0] < _CACHE_TTL:
            return _cached[1]
    cfg = _load()
    with _lock:
        _cached = (time.monotonic(), cfg)
    return cfg


def invalidate() -> None:
    """Gọi sau khi lưu trang Cài đặt để áp dụng ngay."""
    global _cached
    with _lock:
        _cached = None
