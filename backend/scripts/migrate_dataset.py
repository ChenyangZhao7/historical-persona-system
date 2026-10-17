"""One-off dataset clean-up for backend/data/historical.db.

What it fixes
-------------
1. 423 rows were written with `era = 0, period = "analyzed"` as a placeholder,
   which silently classified every on-demand figure as "ancient". They are set
   to `era = NULL, period = "unknown"` instead, and the app now treats unknown
   era as "unclassified" rather than guessing.
2. Degenerate profiles are removed: all-zero vectors (failed extractions),
   all-zero confidence, and flat 0.5 vectors that carry no signal.
3. Duplicate figure names are collapsed (the unique index needs this first).
4. Indexes are created (see database.py) once the data is clean.

A copy of the database is written to backend/data/backup/ before any change.

Usage:
    cd backend
    python scripts/migrate_dataset.py            # dry run, prints what it would do
    python scripts/migrate_dataset.py --apply    # actually change the database
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BACKEND_DIR / "data" / "historical.db"


def _is_degenerate(vector: list, confidence: list) -> str | None:
    """Return a reason string if the profile carries no usable signal."""
    if len(vector) != 10 or len(confidence) != 10:
        return "wrong length"
    if all(v == 0 for v in vector):
        return "all-zero vector"
    if all(c == 0 for c in confidence):
        return "all-zero confidence"
    if len(set(vector)) == 1:
        return "flat vector"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="path to the SQLite database")
    parser.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    if not db_path.exists():
        print(f"database not found: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM figures").fetchone()[0]
    print(f"database : {db_path}")
    print(f"figures  : {total}")
    print(f"mode     : {'APPLY' if args.apply else 'dry run'}\n")

    # ---- 1. degenerate profiles -------------------------------------------------
    junk: list[tuple[int, str, str]] = []
    for row in cur.execute(
        "SELECT f.id, f.name, p.vector, p.confidence FROM figures f JOIN profiles p ON p.figure_id = f.id"
    ):
        reason = _is_degenerate(json.loads(row["vector"]), json.loads(row["confidence"]))
        if reason:
            junk.append((row["id"], row["name"], reason))

    print(f"[1] degenerate profiles to delete: {len(junk)}")
    for figure_id, name, reason in junk:
        print(f"    #{figure_id:<4} {name:<24} {reason}")

    # ---- 2. duplicate names -----------------------------------------------------
    # Junk rows are already scheduled for deletion, so they never "win" a name.
    junk_ids = {figure_id for figure_id, _, _ in junk}
    dupes: list[tuple[int, str]] = []
    seen: dict[str, int] = {}
    for row in cur.execute("SELECT id, name FROM figures ORDER BY id"):
        if row["id"] in junk_ids:
            continue
        key = row["name"].strip().lower()
        if key in seen:
            dupes.append((row["id"], row["name"]))
        else:
            seen[key] = row["id"]

    print(f"\n[2] duplicate-name rows to delete: {len(dupes)}")
    for figure_id, name in dupes:
        print(f"    #{figure_id:<4} {name}  (keeping #{seen[name.strip().lower()]})")

    # ---- 3. era placeholders ----------------------------------------------------
    placeholders = cur.execute(
        "SELECT COUNT(*) FROM figures WHERE era = 0 AND period = 'analyzed'"
    ).fetchone()[0]
    print(f"\n[3] rows with placeholder era=0 / period='analyzed': {placeholders}")
    print("    -> era = NULL, period = 'unknown'")

    deleted_ids = [figure_id for figure_id, _, _ in junk] + [figure_id for figure_id, _ in dupes]
    deleted_ids = sorted(set(deleted_ids))
    print(f"\n[4] total rows removed: {len(deleted_ids)}")

    if not args.apply:
        print("\nDry run only. Re-run with --apply to write these changes.")
        conn.close()
        return 0

    backup_dir = db_path.parent / "backup"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f"{db_path.stem}-{datetime.now():%Y%m%d-%H%M%S}{db_path.suffix}"
    shutil.copy2(db_path, backup)
    print(f"\nbackup written to: {backup}")

    if deleted_ids:
        marks = ",".join("?" * len(deleted_ids))
        cur.execute(f"DELETE FROM profiles WHERE figure_id IN ({marks})", deleted_ids)
        cur.execute(f"DELETE FROM figures WHERE id IN ({marks})", deleted_ids)

    cur.execute("UPDATE figures SET era = NULL, period = 'unknown' WHERE era = 0 AND period = 'analyzed'")

    conn.commit()

    remaining = cur.execute("SELECT COUNT(*) FROM figures").fetchone()[0]
    unknown_era = cur.execute("SELECT COUNT(*) FROM figures WHERE era IS NULL").fetchone()[0]
    print(f"figures after clean-up: {remaining}  (era unknown: {unknown_era})")
    conn.close()
    print("done. run init_db() / start the server to create the indexes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
