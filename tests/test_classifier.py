from app.services.rule_classifier import classify


def test_classify_python():
    assert classify("FastAPI guide", "https://python.org", "Pendientes") in {"python", "ia", "tecnologia"}
