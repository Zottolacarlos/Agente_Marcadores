import sqlite3
from app.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns(cur, table: str, columns: dict[str, str]) -> None:
    """Agrega columnas que falten a una tabla existente (migración liviana).
    `CREATE TABLE IF NOT EXISTS` no altera tablas ya creadas, así que las DBs
    viejas necesitan este ALTER para incorporar campos nuevos sin recrearse."""
    existing = {row["name"] for row in cur.execute(f"PRAGMA table_info({table})")}
    for name, col_type in columns.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {col_type}")


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
            reason TEXT,
            effective_score INTEGER,
            ai_category TEXT,
            ai_reason TEXT,
            ai_confidence REAL
        )
        """
    )
    # Migración para DBs creadas antes de persistir la capa IA: el chat y el
    # dashboard leen estos campos, así que deben existir aunque la tabla sea vieja.
    _ensure_columns(
        cur,
        "bookmarks_analysis",
        {
            "effective_score": "INTEGER",
            "ai_category": "TEXT",
            "ai_reason": "TEXT",
            "ai_confidence": "REAL",
        },
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
