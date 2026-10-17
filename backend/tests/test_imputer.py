import json
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imputer import impute_profile


def _make_row(row_id, name, era, vector, confidence):
    row = MagicMock()
    row.__getitem__ = lambda self, k: {
        "id": row_id, "name": name, "era": era,
        "vector": json.dumps(vector),
        "confidence": json.dumps(confidence),
    }[k]
    return row


TARGET_VEC = [0.8, 0.5, 0.0, 0.7, 0.6, 0.3, 0.9, 0.4, 0.2, 0.1]
TARGET_CONF = [0.9, 0.0, 0.0, 0.8, 0.7, 0.9, 0.8, 0.7, 0.0, 0.0]

DONOR_VEC  = [0.7, 0.6, 0.3, 0.8, 0.5, 0.4, 0.8, 0.5, 0.9, 0.7]
DONOR_CONF = [0.8, 0.9, 0.8, 0.9, 0.8, 0.9, 0.9, 0.8, 0.9, 0.8]


@contextmanager
def _fake_connection(target_row, donor_rows):
    """Stands in for database.connection(), which is a context manager."""
    cursor = MagicMock()
    cursor.fetchone.return_value = target_row
    cursor.fetchall.return_value = donor_rows
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.execute.return_value.fetchone.return_value = target_row
    conn.execute.return_value.fetchall.return_value = donor_rows
    yield conn


def _patch_connection(target_row, donor_rows):
    return patch("imputer.connection", lambda: _fake_connection(target_row, donor_rows))


def test_missing_figure_returns_error():
    with _patch_connection(None, []):
        result = impute_profile(999)
    assert "error" in result


def test_impute_fills_low_confidence_dims():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    donor = _make_row(2, "Donor", 1900, DONOR_VEC, DONOR_CONF)
    with _patch_connection(target, [donor]):
        result = impute_profile(1)

    low_conf_dims = [i for i, c in enumerate(TARGET_CONF) if c < 0.4]
    assert low_conf_dims, "fixture must contain low-confidence dimensions"
    assert result["imputed_from"], "a donor with full confidence should fill something"
    for i in result["imputed_from"]:
        assert i in low_conf_dims


def test_impute_preserves_high_confidence_dims():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    donor = _make_row(2, "Donor", 1900, DONOR_VEC, DONOR_CONF)
    with _patch_connection(target, [donor]):
        result = impute_profile(1)

    for i, conf in enumerate(TARGET_CONF):
        if conf >= 0.4:
            assert result["imputed_vector"][i] == TARGET_VEC[i]
            assert i not in result["imputed_from"]


def test_impute_result_has_required_keys():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    with _patch_connection(target, []):
        result = impute_profile(1)

    for key in ("figure_id", "original_vector", "original_confidence", "imputed_vector", "imputed_from"):
        assert key in result


def test_impute_vector_length_preserved():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    donor = _make_row(2, "Donor", 1900, DONOR_VEC, DONOR_CONF)
    with _patch_connection(target, [donor]):
        result = impute_profile(1)
    assert len(result["imputed_vector"]) == 10


def test_impute_no_donors_returns_original():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    with _patch_connection(target, []):
        result = impute_profile(1)
    assert result["imputed_vector"] == result["original_vector"]
    assert result["imputed_from"] == {}


def test_impute_with_user_vector():
    target = _make_row(1, "Target", 500, TARGET_VEC, TARGET_CONF)
    with _patch_connection(target, []):
        user_vector = [0.6, 0.7, 0.4, 0.5, 0.8, 0.3, 0.7, 0.6, 0.9, 0.8]
        result = impute_profile(1, user_vector=user_vector)

    low_conf_dims = [i for i, c in enumerate(TARGET_CONF) if c < 0.4]
    filled = list(result["imputed_from"].keys())
    assert any(i in low_conf_dims for i in filled)
