from datetime import datetime, timedelta

import pytest

from db.model.chapter_analysis_job import ChapterAnalysisJob
from db.model.chapter_revision import ChapterRevision


def _url(comic, chapter=None, suffix=""):
    base = f"/api/comics/{comic['id']}/chapters"
    return f"{base}/{chapter['id']}{suffix}" if chapter else base


# ── Số chương ─────────────────────────────────────────────────────────────────

def test_float_chapter_number(client, comic):
    r = client.post(_url(comic), json={"number": 30.5, "title": "Ngoại truyện"})
    assert r.status_code == 201
    assert r.json()["number"] == 30.5


def test_duplicate_number_conflict(client, comic, chapter):
    r = client.post(_url(comic), json={"number": 1})
    assert r.status_code == 409


def test_renumber_into_existing_conflict(client, comic, chapter):
    other = client.post(_url(comic), json={"number": 2}).json()
    r = client.put(_url(comic, other), json={"number": 1})
    assert r.status_code == 409


# ── Nội dung, ghi chú ─────────────────────────────────────────────────────────

def test_save_content_and_notes(client, comic, chapter):
    r = client.put(_url(comic, chapter), json={"content": "<p>Xin chào</p>", "notes": "ghi chú"})
    assert r.status_code == 200
    got = client.get(_url(comic, chapter)).json()
    assert got["content"] == "<p>Xin chào</p>"
    assert got["notes"] == "ghi chú"


def test_list_does_not_leak_content(client, comic, chapter):
    client.put(_url(comic, chapter), json={"content": "<p>dài</p>"})
    row = client.get(_url(comic)).json()[0]
    assert "content" not in row


def test_comic_updated_at_bumped(client, comic, chapter):
    before = client.get(f"/api/comics/{comic['id']}").json()["updated_at"]
    client.put(_url(comic, chapter), json={"content": "<p>mới</p>"})
    after = client.get(f"/api/comics/{comic['id']}").json()["updated_at"]
    assert after > before


# ── Lịch sử ───────────────────────────────────────────────────────────────────

def test_first_change_snapshots_old_content(client, comic, chapter):
    client.put(_url(comic, chapter), json={"content": "<p>v1</p>"})  # cũ rỗng → không chụp
    client.put(_url(comic, chapter), json={"content": "<p>v2</p>"})  # lần đầu có cũ → chụp v1
    client.put(_url(comic, chapter), json={"content": "<p>v3</p>"})  # < 10 phút → không chụp
    revs = client.get(_url(comic, chapter, "/revisions")).json()
    assert [r["reason"] for r in revs] == ["auto"]
    detail = client.get(_url(comic, chapter, f"/revisions/{revs[0]['id']}")).json()
    assert detail["content"] == "<p>v1</p>"


def test_snapshot_after_interval(client, comic, chapter, session_factory):
    client.put(_url(comic, chapter), json={"content": "<p>v1</p>"})
    client.put(_url(comic, chapter), json={"content": "<p>v2</p>"})
    # Đẩy bản chụp lùi 11 phút
    with session_factory() as db:
        for rev in db.query(ChapterRevision):
            rev.created_at = datetime.utcnow() - timedelta(minutes=11)
        db.commit()
    client.put(_url(comic, chapter), json={"content": "<p>v3</p>"})
    contents = [
        client.get(_url(comic, chapter, f"/revisions/{r['id']}")).json()["content"]
        for r in client.get(_url(comic, chapter, "/revisions")).json()
    ]
    assert contents == ["<p>v2</p>", "<p>v1</p>"]


def test_manual_snapshot(client, comic, chapter):
    client.put(_url(comic, chapter) + "?snapshot=true", json={"content": "<p>chốt</p>"})
    revs = client.get(_url(comic, chapter, "/revisions")).json()
    assert revs[0]["reason"] == "manual"
    assert revs[0]["char_count"] == len("chốt")


def test_restore_keeps_current(client, comic, chapter):
    client.put(_url(comic, chapter) + "?snapshot=true", json={"content": "<p>bản tốt</p>"})
    client.put(_url(comic, chapter), json={"content": "<p>lỡ xoá</p>"})
    good = client.get(_url(comic, chapter, "/revisions")).json()[-1]

    r = client.post(_url(comic, chapter, f"/revisions/{good['id']}/restore"))
    assert r.status_code == 200
    assert r.json()["content"] == "<p>bản tốt</p>"

    revs = client.get(_url(comic, chapter, "/revisions")).json()
    assert revs[0]["reason"] == "restore"
    assert client.get(_url(comic, chapter, f"/revisions/{revs[0]['id']}")).json()["content"] == "<p>lỡ xoá</p>"


def test_revision_of_other_chapter_404(client, comic, chapter):
    other = client.post(_url(comic), json={"number": 2}).json()
    client.put(_url(comic, other) + "?snapshot=true", json={"content": "<p>x</p>"})
    rev = client.get(_url(comic, other, "/revisions")).json()[0]
    assert client.get(_url(comic, chapter, f"/revisions/{rev['id']}")).status_code == 404


# ── Job cập nhật graph ────────────────────────────────────────────────────────

@pytest.fixture
def graph_on(monkeypatch):
    import services.chapter_analysis as svc

    calls = []
    monkeypatch.setattr(svc, "graph_configured", lambda: True)
    monkeypatch.setattr(svc, "run_chapter_analysis", lambda *a, **k: calls.append(a))
    return calls


def test_saves_coalesce_into_one_pending_job(client, comic, chapter, graph_on, session_factory):
    for i in range(5):
        client.put(_url(comic, chapter), json={"content": f"<p>v{i}</p>"})
    with session_factory() as db:
        jobs = db.query(ChapterAnalysisJob).all()
    assert len(jobs) == 1
    assert jobs[0].status == "pending"
    assert len(graph_on) == 1


def test_no_job_when_content_unchanged(client, comic, chapter, graph_on, session_factory):
    client.put(_url(comic, chapter), json={"content": "<p>a</p>"})
    with session_factory() as db:
        db.query(ChapterAnalysisJob).update({"status": "done"})
        db.commit()
    client.put(_url(comic, chapter), json={"content": "<p>a</p>", "notes": "chỉ sửa ghi chú"})
    with session_factory() as db:
        assert db.query(ChapterAnalysisJob).count() == 1


def test_no_job_when_graph_not_configured(client, comic, chapter, session_factory, monkeypatch):
    import services.chapter_analysis as svc

    monkeypatch.setattr(svc, "graph_configured", lambda: False)
    client.put(_url(comic, chapter), json={"content": "<p>a</p>"})
    with session_factory() as db:
        assert db.query(ChapterAnalysisJob).count() == 0
