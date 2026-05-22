from app.services.rule_classifier import classify


def test_classify_python():
    assert classify("FastAPI guide", "https://python.org", "Pendientes") == "python"


def test_classify_finanzas():
    assert classify("Dólar hoy", "https://dolarhoy.com", "Barra de favoritos/Metalico") == "finanzas"


def test_classify_gaming():
    assert classify("SteamDB", "https://steamdb.info", "Barra de favoritos/Games") == "gaming"


def test_classify_ia():
    assert classify("LangGraph RAG agents", "https://example.com", "IA") == "ia"
