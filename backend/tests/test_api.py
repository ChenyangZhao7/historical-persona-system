"""Integration-style tests using FastAPI TestClient.

External dependencies (database, LLM provider) are mocked, so nothing here
touches the network or the real database.
"""
import json
import os

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("LLM_PROVIDER", "anthropic")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)

SAMPLE_PROFILE = {
    "name": "Julius Caesar",
    "vector": [0.9, 0.5, 0.8, 0.6, 0.7, 0.3, 0.8, 0.9, 0.7, 0.9],
    "confidence": [0.9] * 10,
    "evidence": [f"Evidence {i}" for i in range(10)],
}


def _figure_row():
    row = MagicMock()
    row.__getitem__ = lambda self, k: {
        "id": 1,
        "name": "Caesar",
        "era": -44,
        "period": "ancient",
        "vector": json.dumps([0.5] * 10),
        "confidence": json.dumps([0.8] * 10),
        "evidence": json.dumps(["e"] * 10),
    }[k]
    return row


class _FakeConn:
    """Minimal stand-in for database.connection()'s yielded connection."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self, *args, **kwargs):
        result = MagicMock()
        result.fetchall.return_value = self._rows
        result.fetchone.return_value = self._rows[0] if self._rows else None
        return result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ── GET /figures/ ──────────────────────────────────────────────────────────────

@patch("routers.figures.connection", lambda: _FakeConn([]))
def test_list_figures_returns_list():
    r = client.get("/figures/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@patch("routers.figures.connection", lambda: _FakeConn([_figure_row()]))
def test_list_figures_returns_correct_shape():
    r = client.get("/figures/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Caesar"
    assert len(data[0]["vector"]) == 10
    assert "evidence" in data[0]


@patch("routers.figures.connection", lambda: _FakeConn([_figure_row()]))
def test_list_figures_can_omit_evidence():
    r = client.get("/figures/?evidence=false")
    assert r.status_code == 200
    assert "evidence" not in r.json()[0]


# ── POST /match/ ───────────────────────────────────────────────────────────────

@patch("routers.match.find_matches")
@patch("routers.match.extract_profile")
def test_match_returns_results(mock_extract, mock_find):
    mock_extract.return_value = SAMPLE_PROFILE
    mock_find.return_value = [
        {"id": 1, "name": "Caesar", "era": -44, "period": "ancient", "score": 0.95}
    ]
    payload = {"description": "I am a determined leader who takes bold action.", "top_k": 3}
    r = client.post("/match/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "matches" in data
    assert len(data["matches"]) == 1


def test_match_missing_description_fails():
    r = client.post("/match/", json={"top_k": 3})
    assert r.status_code == 422


# ── POST /predict/ ─────────────────────────────────────────────────────────────

@patch("routers.predict.get_historical_responses")
def test_predict_returns_figures(mock_ghr):
    mock_ghr.return_value = {
        "question": "test question",
        "figures": [
            {"name": "Caesar", "era": -44, "period": "ancient",
             "score": 0.9, "type": "ancient", "response": "I fought."}
        ],
    }
    r = client.post("/predict/", json={"question": "What to do?", "user_vector": [0.5] * 10})
    assert r.status_code == 200
    assert r.json()["figures"][0]["name"] == "Caesar"


def test_predict_missing_question_fails():
    r = client.post("/predict/", json={"user_vector": [0.5] * 10})
    assert r.status_code == 422


# ── POST /reconstruct/ ────────────────────────────────────────────────────────

@patch("routers.reconstruct.reconstruct_history")
def test_reconstruct_returns_narratives(mock_rh):
    mock_rh.return_value = {
        "action": "left career",
        "figures": [
            {"name": "Caesar", "era": -44, "period": "ancient",
             "score": 0.88, "narrative": "He crossed the Rubicon..."}
        ],
    }
    r = client.post("/reconstruct/", json={"action": "I left my job", "source_vector": [0.5] * 10})
    assert r.status_code == 200
    assert "narrative" in r.json()["figures"][0]


# ── GET / (health check) ───────────────────────────────────────────────────────

def test_root_returns_200():
    r = client.get("/")
    assert r.status_code == 200

# ── input validation (regression: short vectors / negative top_k) ─────────────

def test_predict_rejects_short_vector():
    r = client.post("/predict/", json={"question": "hi", "user_vector": [0.5] * 3})
    assert r.status_code == 422

def test_predict_rejects_long_vector():
    r = client.post("/predict/", json={"question": "hi", "user_vector": [0.5] * 11})
    assert r.status_code == 422

def test_reconstruct_rejects_short_vector():
    r = client.post("/reconstruct/", json={"action": "x", "source_vector": [0.5] * 9})
    assert r.status_code == 422

def test_match_rejects_nonpositive_top_k():
    r = client.post("/match/", json={"description": "x", "top_k": -1})
    assert r.status_code == 422

def test_reverse_rejects_nonpositive_top_k():
    assert client.get("/reverse/Caesar?top_k=0").status_code == 422
    assert client.get("/reverse/Caesar?top_k=-3").status_code == 422
