import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    schema = SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.close()


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
