import sqlite3
from app.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            normalized_url TEXT,
            folder_path TEXT,
            status TEXT,
            category TEXT,
            score INTEGER,
            recommended_action TEXT,
            duplicate INTEGER,
            reason TEXT
        )
        """
    )
    conn.commit()
    conn.close()
