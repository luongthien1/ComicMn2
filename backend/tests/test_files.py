import pytest
from fastapi import HTTPException

from api import get_file


def test_traversal_blocked(client, tmp_path):
    # Hàm gọi trực tiếp — HTTP client tự chuẩn hoá "../" nên không thử được qua URL
    (tmp_path / "secret.env").write_text("GEMINI_API_KEY=x")
    with pytest.raises(HTTPException) as e:
        get_file("../secret.env")
    assert e.value.status_code == 404


def test_traversal_blocked_encoded(client, tmp_path):
    (tmp_path / "secret.env").write_text("GEMINI_API_KEY=x")
    r = client.get("/api/files/%2E%2E/secret.env")
    assert r.status_code == 404


def test_missing_file_404(client):
    assert client.get("/api/files/khong-co.png").status_code == 404


def test_upload_image_roundtrip(client):
    r = client.post("/api/upload", files={"file": ("a.png", b"\x89PNG data", "image/png")})
    assert r.status_code == 200
    url = r.json()["url"]
    got = client.get(url)
    assert got.status_code == 200
    assert got.content == b"\x89PNG data"


def test_upload_rejects_non_image(client):
    r = client.post("/api/upload", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 415


def test_upload_rejects_too_large(client, monkeypatch, tmp_path):
    from core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)
    big = b"0" * (1024 * 1024 + 1)
    r = client.post("/api/upload", files={"file": ("big.png", big, "image/png")})
    assert r.status_code == 413
    # File dở dang phải bị xoá
    assert not any((tmp_path / "media").glob("*.png"))
