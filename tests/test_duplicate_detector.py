from app.services.duplicate_detector import detect_duplicates


def test_detect_duplicates():
    dups = detect_duplicates(["a", "b", "a"])
    assert "a" in dups
