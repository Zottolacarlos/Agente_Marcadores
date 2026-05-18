from app.services.priority_scorer import score_bookmark


def test_priority_score_high():
    score, action, _ = score_bookmark("python", "OK", "Pendientes", False, "Backend API", "https://example.com")
    assert score >= 70
    assert action in {"ver_esta_semana", "ver_luego"}
