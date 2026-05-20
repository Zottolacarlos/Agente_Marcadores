from app.database import get_connection
from app.models.bookmark import BookmarkAnalysis


class SQLiteRepository:
    def save_analysis(self, rows: list[BookmarkAnalysis]) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM bookmarks_analysis")
        cur.executemany(
            """
            INSERT INTO bookmarks_analysis
            (title,url,normalized_url,folder_path,status,category,score,recommended_action,duplicate,reason)
            VALUES (?,?,?,?,?,?,?,?,?,?)
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
                )
                for r in rows
            ],
        )
        conn.commit()
        conn.close()

    def list_bookmarks(self) -> list[dict]:
        conn = get_connection()
        cur = conn.cursor()
        data = [dict(x) for x in cur.execute("SELECT * FROM bookmarks_analysis ORDER BY score DESC").fetchall()]
        conn.close()
        return data
