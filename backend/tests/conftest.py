"""Test chạy trên SQLite in-memory — không đụng PostgreSQL/Neo4j/Ollama thật."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import db.model  # noqa: F401 — đăng ký mọi bảng vào metadata
from db.migrations.base import Base
from libs.database.connect import get_db
from main import app


@pytest.fixture(autouse=True)
def no_external_services(monkeypatch):
    """Mặc định tắt graph: không job nền, không gọi Neo4j/Ollama thật."""
    import importlib

    import services.chapter_analysis as svc

    # api.comics xuất biến `router` (APIRouter) che mất module cùng tên
    router_mod = importlib.import_module("api.comics.router")
    monkeypatch.setattr(svc, "graph_configured", lambda: False)
    monkeypatch.setattr(router_mod, "graph_configured", lambda: False)


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


@pytest.fixture
def client(session_factory, monkeypatch, tmp_path):
    def _get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    from core.config import settings

    monkeypatch.setattr(settings, "media_dir", str(tmp_path / "media"))
    app.dependency_overrides[get_db] = _get_db
    # Không có TestClient context manager → lifespan (dọn job, Neo4j) không chạy
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def comic(client):
    r = client.post("/api/comics/", json={"title": "Truyện thử"})
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def chapter(client, comic):
    r = client.post(f"/api/comics/{comic['id']}/chapters", json={"number": 1, "title": "Mở đầu"})
    assert r.status_code == 201
    return r.json()
