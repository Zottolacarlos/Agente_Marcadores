from fastapi.testclient import TestClient

from app.main import app
from app.models.ai import AIBookmarkClassification
from app.services import ai_classifier

client = TestClient(app)

SAMPLE = (
    b"<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p><DT><H3>Pendientes</H3>"
    b'<DL><p><DT><A HREF="https://fastapi.tiangolo.com">FastAPI</A></DL></DL>'
)


def test_home_shows_ai_checkbox():
    r = client.get("/")
    assert r.status_code == 200
    assert 'name="use_ai"' in r.text


def test_analyze_with_ai_renders_banner(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: True)
    cls = AIBookmarkClassification(
        category="python", subcategory="web", intent="aprender",
        priority=90, recommended_action="leer_hoy", reason="relevante", confidence=0.95,
    )
    monkeypatch.setattr(ai_classifier, "classify_bookmarks_batch", lambda payloads: [cls for _ in payloads])
    r = client.post(
        "/analyze",
        data={"target_folder": "Pendientes", "skip_validation": "true", "use_ai": "true"},
        files={"file": ("b.html", SAMPLE, "text/html")},
    )
    assert r.status_code == 200
    assert "IA activada" in r.text
    assert "pill-ai" in r.text


def test_analyze_without_ai_has_no_banner():
    r = client.post(
        "/analyze",
        data={"target_folder": "Pendientes", "skip_validation": "true"},
        files={"file": ("b.html", SAMPLE, "text/html")},
    )
    assert r.status_code == 200
    assert "IA activada" not in r.text


def test_more_than_ten_results_show_toggle():
    links = "".join(
        f'<DT><A HREF="https://example.com/{i}">Link {i}</A>' for i in range(12)
    )
    html = (
        b"<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p><DT><H3>Pendientes</H3><DL><p>"
        + links.encode()
        + b"</DL></DL>"
    )
    r = client.post(
        "/analyze",
        data={"target_folder": "Pendientes", "skip_validation": "true"},
        files={"file": ("b.html", html, "text/html")},
    )
    assert r.status_code == 200
    assert "Ver más" in r.text
    assert "extra-row" in r.text


def test_analyze_renders_schedule_section():
    r = client.post(
        "/analyze",
        data={"target_folder": "Pendientes", "skip_validation": "true"},
        files={"file": ("b.html", SAMPLE, "text/html")},
    )
    assert r.status_code == 200
    assert "Cronograma sugerido" in r.text
