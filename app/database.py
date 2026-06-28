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
    # Estado persistente del trabajo de curaduría: guarda la ÚLTIMA corrida (no un
    # historial día-a-día) para mostrar un dashboard al reabrir la app.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            updated_at TEXT,
            params TEXT,
            summary TEXT
        )
        """
    )
    conn.commit()
    conn.close()
