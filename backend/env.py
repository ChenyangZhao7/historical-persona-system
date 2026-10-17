"""Minimal .env loader.

Cross-platform replacement for the old `source .env` in start.sh: no external
dependency, no shell required. Existing environment variables always win, so
`export ANTHROPIC_API_KEY=...` still overrides the file.
"""
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _candidate_files():
    return (_REPO_ROOT / ".env", Path(__file__).resolve().parent / ".env")


def load_env(path: Path | None = None) -> list[Path]:
    """Load KEY=VALUE pairs from .env. Returns the files that were read."""
    files = [path] if path else [p for p in _candidate_files() if p.exists()]
    loaded = []
    for file in files:
        if not file.exists():
            continue
        for raw in file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        loaded.append(file)
    return loaded
