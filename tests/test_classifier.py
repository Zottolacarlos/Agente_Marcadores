from app.services.rule_classifier import classify


def test_classify_python():
    assert classify("FastAPI guide", "https://python.org", "Pendientes") == "python"


def test_classify_finanzas():
    assert classify("Dólar hoy", "https://dolarhoy.com", "Barra de favoritos/Metalico") == "finanzas"


def test_classify_gaming():
    assert classify("SteamDB", "https://steamdb.info", "Barra de favoritos/Games") == "gaming"


def test_classify_ia():
    assert classify("LangGraph RAG agents", "https://example.com", "IA") == "ia"


def test_no_false_positive_from_url_id():
    # "s3" dentro de un ID de YouTube no debe clasificar como aws.
    assert classify(
        "Cómo armar un muñeco de Transformers",
        "https://www.youtube.com/watch?v=Lk3s3Qabc",
        "Pendientes",
    ) != "aws"


def test_no_false_positive_word_boundary():
    # "rag" dentro de "storage" no debe clasificar como ia.
    assert classify("Mi storage personal", "https://blog.com", "Pendientes") != "ia"


def test_unknown_stays_unknown():
    assert classify("Receta de pan casero", "https://cocina.com/post?id=lambda99", "Pendientes") == "desconocido"


def test_domain_fallback_youtube():
    assert classify("Un video cualquiera", "https://youtu.be/abc123", "Pendientes") == "entretenimiento"
