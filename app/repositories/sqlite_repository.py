import json

from app.database import get_connection
from app.models.analysis import AnalysisSummary
from app.models.bookmark import BookmarkAnalysis


class SQLiteRepository:
    def save_analysis(self, rows: list[BookmarkAnalysis]) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM bookmarks_analysis")
        cur.executemany(
            """
            INSERT INTO bookmarks_analysis
            (title,url,normalized_url,folder_path,status,category,score,recommended_action,duplicate,reason,
             effective_score,ai_category,ai_reason,ai_confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                (
                    r.title,
                    r.url,
                    r.normalized_url,
                    r.folder_path,
                    r.status,
                    r.category,
                    r.score,
                    r.recommended_action,
                    int(r.duplicate),
                    r.reason,
                    # Persistimos la capa IA (categoría/razón/confianza) y el score
                    # efectivo (blended) para que el chat y el dashboard vean lo mismo
                    # que la corrida, no solo la clasificación por reglas.
                    r.effective_score,
                    r.ai.category if r.ai else None,
                    r.ai.reason if r.ai else None,
                    r.ai.confidence if r.ai else None,
                )
                for r in rows
            ],
        )
        conn.commit()
        conn.close()

    def list_bookmarks(self) -> list[dict]:
        conn = get_connection()
        cur = conn.cursor()
        # Ordena por score efectivo (blended con IA cuando existe) y cae al score
        # local si la fila es previa a la migración (effective_score NULL).
        data = [
            dict(x)
            for x in cur.execute(
                "SELECT * FROM bookmarks_analysis ORDER BY COALESCE(effective_score, score) DESC"
            ).fetchall()
        ]
        conn.close()
        return data

    def save_state(self, summary: AnalysisSummary, params: dict, updated_at: str) -> None:
        """Persiste la última corrida (una sola fila) para el dashboard."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO analysis_state (id, updated_at, params, summary)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at,
                params=excluded.params, summary=excluded.summary
            """,
            (updated_at, json.dumps(params, ensure_ascii=False), summary.model_dump_json()),
        )
        conn.commit()
        conn.close()

    def load_state(self) -> dict | None:
        """Devuelve {updated_at, params, summary} de la última corrida, o None."""
        conn = get_connection()
        cur = conn.cursor()
        row = cur.execute("SELECT updated_at, params, summary FROM analysis_state WHERE id=1").fetchone()
        conn.close()
        if row is None:
            return None
        return {
            "updated_at": row["updated_at"],
            "params": json.loads(row["params"]),
            "summary": AnalysisSummary.model_validate_json(row["summary"]),
        }
