from app import database
from app.models.ai import AIBookmarkClassification
from app.models.bookmark import BookmarkAnalysis
from app.repositories.sqlite_repository import SQLiteRepository


def _analysis(**over):
    base = dict(
        title="Tuto de push/fold",
        url="https://ej.com/pkr1",
        normalized_url="https://ej.com/pkr1",
        folder_path="Pkr/NUEVOS TUTOS POKER",
        status="OK",
        category="desconocido",
        score=40,
        recommended_action="ver_luego",
        duplicate=False,
        reason="base 40",
        effective_score=72,
    )
    base.update(over)
    return BookmarkAnalysis(**base)


def test_save_analysis_persiste_capa_ia(tmp_path, monkeypatch):
    # DB temporal aislada.
    monkeypatch.setattr(database.settings, "database_path", tmp_path / "test.db")
    database.init_db()

    ai = AIBookmarkClassification(
        category="poker", subcategory=None, intent="estudiar",
        priority=80, recommended_action="ver_luego",
        reason="Tutorial de estrategia de póker.", confidence=0.9,
    )
    repo = SQLiteRepository()
    repo.save_analysis([_analysis(ai=ai), _analysis(url="https://ej.com/pkr2", effective_score=30)])

    rows = repo.list_bookmarks()
    assert len(rows) == 2
    # Ordenado por score efectivo desc (72 antes que 30).
    assert rows[0]["effective_score"] == 72
    # La capa IA quedó persistida en la fila.
    assert rows[0]["ai_category"] == "poker"
    assert rows[0]["ai_reason"] == "Tutorial de estrategia de póker."
    assert abs(rows[0]["ai_confidence"] - 0.9) < 1e-6
    # Fila sin IA: los campos IA quedan en NULL, no rompe.
    assert rows[1]["ai_category"] is None


def test_migracion_agrega_columnas_a_db_vieja(tmp_path, monkeypatch):
    monkeypatch.setattr(database.settings, "database_path", tmp_path / "old.db")
    # Simula una DB previa: tabla SIN las columnas de la capa IA.
    conn = database.get_connection()
    conn.execute(
        """
        CREATE TABLE bookmarks_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, url TEXT, normalized_url TEXT, folder_path TEXT,
            status TEXT, category TEXT, score INTEGER, recommended_action TEXT,
            duplicate INTEGER, reason TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    # init_db debe migrar (ALTER TABLE) sin recrear ni perder datos.
    database.init_db()
    cols = {r["name"] for r in database.get_connection().execute("PRAGMA table_info(bookmarks_analysis)")}
    assert {"effective_score", "ai_category", "ai_reason", "ai_confidence"} <= cols
