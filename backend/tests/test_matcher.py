import math
import json
import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.matcher import cosine_similarity, weighted_cosine_similarity, find_matches


# ── cosine_similarity ──────────────────────────────────────────────────────────

def test_cosine_identical_vectors():
    v = [0.5, 0.3, 0.8, 0.1, 0.9, 0.2, 0.6, 0.7, 0.4, 0.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)

def test_cosine_orthogonal_vectors():
    a = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    b = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)

def test_cosine_opposite_vectors():
    a = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    b = [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert cosine_similarity(a, b) == pytest.approx(-1.0)

def test_cosine_zero_vector_returns_zero():
    a = [0] * 10
    b = [0.5] * 10
    assert cosine_similarity(a, b) == 0.0

def test_cosine_both_zero_vectors():
    assert cosine_similarity([0]*10, [0]*10) == 0.0

def test_cosine_range():
    a = [0.1, 0.9, 0.3, 0.7, 0.5, 0.2, 0.8, 0.4, 0.6, 0.0]
    b = [0.9, 0.1, 0.7, 0.3, 0.5, 0.8, 0.2, 0.6, 0.4, 1.0]
    score = cosine_similarity(a, b)
    assert -1.0 <= score <= 1.0

def test_cosine_symmetry():
    a = [0.2, 0.5, 0.8, 0.1, 0.3, 0.7, 0.4, 0.9, 0.6, 0.0]
    b = [0.6, 0.2, 0.4, 0.9, 0.1, 0.5, 0.8, 0.3, 0.7, 0.5]
    assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))


# ── weighted_cosine_similarity ─────────────────────────────────────────────────

def test_weighted_uniform_weights_matches_unweighted():
    a = [0.3, 0.7, 0.5, 0.2, 0.9, 0.1, 0.6, 0.4, 0.8, 0.0]
    b = [0.7, 0.3, 0.5, 0.8, 0.1, 0.9, 0.4, 0.6, 0.2, 1.0]
    w = [1.0] * 10
    assert weighted_cosine_similarity(a, b, w) == pytest.approx(cosine_similarity(a, b))

def test_weighted_zero_weight_zeroes_dimension():
    # If we zero out all dimensions except the first, result is cosine of just dim 0
    a = [1.0] + [0.5] * 9
    b = [1.0] + [0.0] * 9
    w = [1.0] + [0.0] * 9
    result = weighted_cosine_similarity(a, b, w)
    assert result == pytest.approx(1.0)  # only first dim matters: [1]*[1] / (1*1) = 1


# ── find_matches ───────────────────────────────────────────────────────────────

MOCK_PROFILES = [
    {"id": 1, "name": "Caesar", "era": -44, "period": "Ancient",
     "vector": json.dumps([0.9, 0.5, 0.8, 0.6, 0.7, 0.3, 0.8, 0.9, 0.7, 0.9]),
     "confidence": json.dumps([0.9] * 10)},
    {"id": 2, "name": "Gandhi", "era": 1948, "period": "Modern",
     "vector": json.dumps([0.2, 0.8, 0.1, 0.7, 0.5, 0.2, 0.1, 0.9, 0.4, 0.6]),
     "confidence": json.dumps([0.9] * 10)},
    {"id": 3, "name": "Napoleon", "era": 1821, "period": "Modern",
     "vector": json.dumps([0.8, 0.4, 0.7, 0.5, 0.8, 0.6, 0.9, 0.8, 0.6, 0.9]),
     "confidence": json.dumps([0.9] * 10)},
]

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_returns_top_k(mock_profiles):
    query = [0.9, 0.5, 0.8, 0.6, 0.7, 0.3, 0.8, 0.9, 0.7, 0.9]
    results = find_matches(query, top_k=2)
    assert len(results) == 2

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_sorted_descending(mock_profiles):
    query = [0.5] * 10
    results = find_matches(query, top_k=3)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_exact_match_scores_highest(mock_profiles):
    caesar_vector = json.loads(MOCK_PROFILES[0]["vector"])
    results = find_matches(caesar_vector, top_k=3)
    assert results[0]["name"] == "Caesar"
    assert results[0]["score"] == pytest.approx(1.0, abs=0.01)

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_respects_top_k_larger_than_db(mock_profiles):
    query = [0.5] * 10
    results = find_matches(query, top_k=100)
    assert len(results) == len(MOCK_PROFILES)

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_result_has_required_fields(mock_profiles):
    results = find_matches([0.5] * 10, top_k=1)
    r = results[0]
    assert "id" in r
    assert "name" in r
    assert "era" in r
    assert "score" in r

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_invalid_weights_uses_default(mock_profiles):
    query = [0.5] * 10
    r1 = find_matches(query, top_k=3, weights=None)
    r2 = find_matches(query, top_k=3, weights=[1.0] * 10)
    assert [r["name"] for r in r1] == [r["name"] for r in r2]

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_wrong_length_weights_uses_default(mock_profiles):
    query = [0.5] * 10
    # 5-element weights should fall back to default (no crash)
    results = find_matches(query, top_k=3, weights=[1.0] * 5)
    assert len(results) == 3
