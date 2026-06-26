from app.models.ai import AIBookmarkClassification
from app.models.bookmark import Bookmark
from app.services import ai_classifier, analyzer


def _bookmarks():
    return [
        Bookmark(title="FastAPI guide", url="https://example.com/a", folder_path="Pendientes"),
        Bookmark(title="Compra Gamer", url="https://compragamer.com", folder_path="Pendientes"),
    ]


def _fake_ai(payload):
    return AIBookmarkClassification(
        category="compras",
        subcategory="hardware_gaming",
        intent="posible compra futura",
        priority=45,
        recommended_action="ver_luego",
        reason="Tienda de hardware guardada como referencia de compra.",
        confidence=0.86,
    )


def test_ai_disabled_by_default():
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True)
    assert summary.ai_used is False
    assert summary.ai_enriched == 0
    assert all(item.ai is None for item in summary.top_recommended)


def test_use_ai_without_api_key_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: False)
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True, use_ai=True)
    assert summary.ai_used is False
    assert summary.ai_enriched == 0
    assert summary.warning is not None and "IA" in summary.warning
    # El análisis local sigue intacto.
    assert summary.total == 2


def test_ai_response_enriches_results(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai_classifier, "classify_bookmark_with_ai", _fake_ai)
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True, use_ai=True)
    assert summary.ai_used is True
    assert summary.ai_enriched == 2
    enriched = summary.top_recommended[0]
    assert enriched.ai is not None
    assert enriched.ai.category == "compras"
    # La categoría local NO se pisa (la IA es aditiva).
    assert enriched.category != "" and enriched.score >= 0


def test_invalid_ai_response_keeps_local_result(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai_classifier, "classify_bookmark_with_ai", lambda payload: None)
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True, use_ai=True)
    assert summary.ai_used is True
    assert summary.ai_enriched == 0
    assert all(item.ai is None for item in summary.top_recommended)


def test_is_ai_available_false_without_key(monkeypatch):
    monkeypatch.setattr(ai_classifier.settings, "openai_api_key", None)
    assert ai_classifier.is_ai_available() is False


def test_classify_returns_none_when_unavailable(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: False)
    assert ai_classifier.classify_bookmark_with_ai({"title": "x"}) is None


_SAMPLE_PROFILE = """# Perfil

## 7. Taxonomía de categorías

```text
ia
python
windev
desconocido
```
"""


def test_parse_taxonomy_from_profile():
    assert ai_classifier._parse_taxonomy(_SAMPLE_PROFILE) == ["ia", "python", "windev", "desconocido"]


def test_load_profile_and_taxonomy(tmp_path, monkeypatch):
    p = tmp_path / "perfil.md"
    p.write_text(_SAMPLE_PROFILE, encoding="utf-8")
    monkeypatch.setattr(ai_classifier.settings, "perfil_path", p)
    assert ai_classifier.load_profile() is not None
    assert "windev" in ai_classifier.load_taxonomy()


def test_taxonomy_falls_back_when_no_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_classifier.settings, "perfil_path", tmp_path / "no-existe.md")
    assert ai_classifier.load_profile() is None
    assert ai_classifier.load_taxonomy() == ai_classifier.DEFAULT_TAXONOMY


def test_enforce_taxonomy_coerces_unknown():
    taxonomy = ["ia", "python", "desconocido"]
    assert ai_classifier.enforce_taxonomy("python", taxonomy) == "python"
    # Categoría alucinada fuera de la lista -> desconocido.
    assert ai_classifier.enforce_taxonomy("tecnología", taxonomy) == "desconocido"


def test_profile_is_injected_in_system_prompt(tmp_path, monkeypatch):
    p = tmp_path / "perfil.md"
    p.write_text(_SAMPLE_PROFILE, encoding="utf-8")
    monkeypatch.setattr(ai_classifier.settings, "perfil_path", p)
    prompt = ai_classifier.build_system_prompt()
    assert "PERFIL DEL USUARIO" in prompt
    assert "windev" in prompt


def test_low_confidence_is_counted(monkeypatch):
    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: True)

    def _low_conf(payload):
        return AIBookmarkClassification(
            category="ia", subcategory=None, intent="x", priority=50,
            recommended_action="revisar_manual", reason="dudoso", confidence=0.3,
        )

    monkeypatch.setattr(ai_classifier, "classify_bookmark_with_ai", _low_conf)
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True, use_ai=True)
    assert summary.ai_low_confidence >= 1
    # IA dudosa NO debe mezclarse: el score efectivo queda igual al local.
    for item in summary.top_recommended:
        assert item.effective_score == item.score


def test_blending_applies_when_confident(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(ai_classifier, "is_ai_available", lambda: True)

    def _hi(payload):
        return AIBookmarkClassification(
            category="ia", subcategory=None, intent="x", priority=95,
            recommended_action="leer_hoy", reason="muy relevante", confidence=0.95,
        )

    monkeypatch.setattr(ai_classifier, "classify_bookmark_with_ai", _hi)
    summary = analyzer.run_analysis(_bookmarks(), "Pendientes", skip_validation=True, use_ai=True)
    top = summary.top_recommended[0]
    assert top.ai is not None
    w = settings.ai_blend_weight
    expected = max(0, min(100, round((1 - w) * top.score + w * 95)))
    assert top.effective_score == expected
