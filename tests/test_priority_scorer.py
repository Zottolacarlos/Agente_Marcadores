from app.services.priority_scorer import score_bookmark


def test_priority_score_high():
    score, action, _ = score_bookmark("python", "OK", "Pendientes", False, "Backend API", "https://example.com")
    assert score >= 70
    assert action in {"ver_esta_semana", "ver_luego"}


def test_priority_skip_validation_is_not_penalized():
    score, action, reason = score_bookmark("python", "NOT_VALIDATED", "Pendientes", False, "FastAPI", "https://example.com")
    assert score >= 70
    assert action == "ver_esta_semana"
    assert "validación omitida" in reason


def test_priority_broken_link_goes_to_review():
    _, action, _ = score_bookmark("finanzas", "BROKEN", "Metalico", False, "Binance", "https://example.com")
    assert action == "revisar_o_borrar"
