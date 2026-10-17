import os
import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_env_path = os.environ.get("DATABASE_PATH")
DB_PATH = Path(_env_path) if _env_path else Path(__file__).parent / "data" / "historical.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    """Context manager that always closes the connection, including on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS figures (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    era       INTEGER,
    period    TEXT,
    source    TEXT,
    raw_text  TEXT
);

CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY,
    figure_id   INTEGER NOT NULL REFERENCES figures(id) ON DELETE CASCADE,
    vector      TEXT NOT NULL,
    confidence  TEXT NOT NULL,
    evidence    TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One profile per figure, and no two figures with the same name (case-insensitive).
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_figure ON profiles(figure_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_figures_name ON figures(name COLLATE NOCASE);
"""


BUNDLED_DB = Path(__file__).parent / "data" / "historical.db"


def _seed_from_bundle() -> None:
    """Copy the shipped database to DATABASE_PATH when the target is empty.

    Deploys mount a fresh volume at DATABASE_PATH, so without this the app
    starts against an empty file and looks broken.
    """
    if DB_PATH == BUNDLED_DB or not BUNDLED_DB.exists() or DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUNDLED_DB, DB_PATH)


def init_db():
    _seed_from_bundle()
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
