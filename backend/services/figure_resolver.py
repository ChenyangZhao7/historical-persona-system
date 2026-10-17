import json
import sqlite3

from database import connection
from services.extractor import extract_profile
from services.wiki_fetcher import fetch_wikipedia_text

_SELECT_FIGURE = """
    SELECT f.id, f.name, f.era, f.raw_text, p.vector, p.confidence
    FROM figures f
    JOIN profiles p ON p.figure_id = f.id
    WHERE {where}
"""


def _fetch_by_name(cursor, name: str):
    cursor.execute(_SELECT_FIGURE.format(where="f.name = ? COLLATE NOCASE"), (name,))
    return cursor.fetchone()


def resolve_figure(name: str) -> dict | None:
    """Look a figure up by name, extracting a profile from Wikipedia on a miss.

    Figures discovered this way have no known era, so `era` stays NULL and
    `period` is "unknown". Callers that need a century must therefore treat
    NULL as "unclassified" instead of guessing.
    """
    name = name.strip()

    with connection() as conn:
        cursor = conn.cursor()
        figure = _fetch_by_name(cursor, name)
        if figure:
            return dict(figure)

        text = fetch_wikipedia_text(name)
        if not text:
            return None

        profile = extract_profile(name, text)

        try:
            cursor.execute(
                "INSERT INTO figures (name, era, period, source, raw_text) VALUES (?, NULL, ?, ?, ?)",
                (name, "unknown", "Wikipedia", text),
            )
        except sqlite3.IntegrityError:
            # Another request inserted the same figure concurrently.
            existing = _fetch_by_name(cursor, name)
            return dict(existing) if existing else None

        figure_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO profiles (figure_id, vector, confidence, evidence) VALUES (?, ?, ?, ?)",
            (
                figure_id,
                json.dumps(profile["vector"]),
                json.dumps(profile["confidence"]),
                json.dumps(profile["evidence"]),
            ),
        )

        cursor.execute(_SELECT_FIGURE.format(where="f.id = ?"), (figure_id,))
        return dict(cursor.fetchone())
