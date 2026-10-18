import math
import json
import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.matcher import (
    DIMENSIONS,
    MIN_KNOWN_DIMENSIONS,
    cosine_similarity,
    weighted_cosine_similarity,
    find_matches,
    dimension_breakdown,
    is_comparable,
    mean_closeness,
    known_dimensions,
)


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

def test_cosine_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        cosine_similarity([0.5] * 3, [0.5] * 10)

def test_weighted_cosine_mismatched_weights_raises():
    with pytest.raises(ValueError):
        weighted_cosine_similarity([0.5] * 10, [0.5] * 10, [1.0] * 5)


# ── dimension_breakdown ────────────────────────────────────────────────────────

def test_dimension_breakdown_has_one_row_per_dimension():
    breakdown = dimension_breakdown([0.5] * 10, [0.5] * 10)
    assert len(breakdown) == 10
    assert [d["dimension"] for d in breakdown] == DIMENSIONS

def test_dimension_breakdown_identical_vectors_agree_fully():
    breakdown = dimension_breakdown([0.4] * 10, [0.4] * 10)
    assert all(d["closeness"] == 1.0 for d in breakdown)
    assert all(d["gap"] == 0.0 for d in breakdown)

def test_dimension_breakdown_closeness_is_one_minus_gap():
    breakdown = dimension_breakdown([0.9] * 10, [0.3] * 10)
    assert all(d["gap"] == pytest.approx(0.6) for d in breakdown)
    assert all(d["closeness"] == pytest.approx(0.4) for d in breakdown)

def test_dimension_breakdown_keeps_original_values():
    breakdown = dimension_breakdown([0.9] * 10, [0.3] * 10)
    assert breakdown[0]["query"] == 0.9
    assert breakdown[0]["figure"] == 0.3


# ── mean_closeness / known_dimensions ─────────────────────────────────────────

def test_mean_closeness_ignores_undocumented_dimensions():
    # Two dimensions with evidence that agree exactly, eight the profile knows
    # nothing about. Counting those eight as agreement would have reported 0.6.
    confidence = [1.0, 1.0] + [0.0] * 8
    breakdown = dimension_breakdown([0.5] * 10, [0.5, 0.5] + [0.0] * 8,
                                    figure_confidence=confidence)
    assert mean_closeness(breakdown) == pytest.approx(1.0)

def test_mean_closeness_is_zero_when_nothing_is_documented():
    breakdown = dimension_breakdown([0.5] * 10, [0.5] * 10,
                                    figure_confidence=[0.0] * 10)
    assert mean_closeness(breakdown) == 0.0

def test_mean_closeness_without_confidence_weights_every_dimension_equally():
    breakdown = dimension_breakdown([0.5] * 10, [0.4] * 10)
    assert mean_closeness(breakdown) == pytest.approx(0.9)

def test_mean_closeness_respects_user_weights():
    breakdown = dimension_breakdown([0.5] * 10, [0.0] * 10)  # 0.5 agreement everywhere
    breakdown[0] = {**breakdown[0], "closeness": 1.0}          # except dimension 0
    assert mean_closeness(breakdown) == pytest.approx(0.55)
    assert mean_closeness(breakdown, [10] + [1] * 9) > mean_closeness(breakdown)

@patch("services.matcher.get_all_profiles")
def test_find_matches_weights_change_the_order(mock_profiles):
    mock_profiles.return_value = [
        {"id": 1, "name": "Front-half", "era": 1, "period": "x",
         "vector": json.dumps([0.5] * 5 + [0.0] * 5), "confidence": json.dumps([0.9] * 10)},
        {"id": 2, "name": "Back-half", "era": 1, "period": "x",
         "vector": json.dumps([0.0] * 5 + [0.5] * 5), "confidence": json.dumps([0.9] * 10)},
    ]
    query = [0.5] * 10
    front = find_matches(query, top_k=2, weights=[2, 2, 2, 2, 2, 0, 0, 0, 0, 0])
    back = find_matches(query, top_k=2, weights=[0, 0, 0, 0, 0, 2, 2, 2, 2, 2])
    assert front[0]["name"] == "Front-half"
    assert back[0]["name"] == "Back-half"

def test_known_dimensions_counts_only_documented_ones():
    confident = dimension_breakdown([0.5] * 10, [0.5] * 10, figure_confidence=[0.9] * 10)
    assert known_dimensions(confident) == 10
    partial = dimension_breakdown([0.5] * 10, [0.5] * 10,
                                  figure_confidence=[0.9, 0.8] + [0.0] * 8)
    assert known_dimensions(partial) == 2


# ── coverage ─────────────────────────────────────────────────────────────────

def test_is_comparable_requires_most_dimensions():
    complete = dimension_breakdown([0.5] * 10, [0.5] * 10, figure_confidence=[0.9] * 10)
    assert is_comparable(complete)

    barely = dimension_breakdown([0.5] * 10, [0.5] * 10,
                                 figure_confidence=[0.9, 0.9, 0.9, 0.9, 0.9, 0.9] + [0.0] * 4)
    assert known_dimensions(barely) == MIN_KNOWN_DIMENSIONS
    assert is_comparable(barely)

    too_thin = dimension_breakdown([0.5] * 10, [0.5] * 10,
                                   figure_confidence=[0.9, 0.9] + [0.0] * 8)
    assert not is_comparable(too_thin)

def test_find_matches_skips_incomplete_profiles():
    query = [0.5] * 10
    # Caesar keeps his profile; Gandhi has evidence on only two dimensions.
    profiles = [
        dict(MOCK_PROFILES[0]),
        {**MOCK_PROFILES[1], "confidence": json.dumps([0.9, 0.9] + [0.0] * 8)},
    ]
    with patch("services.matcher.get_all_profiles", return_value=profiles):
        results = find_matches(query, top_k=5)
    assert [r["name"] for r in results] == ["Caesar"]


# ── ordering ─────────────────────────────────────────────────────────────────

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_sorted_by_closeness_not_cosine(mock_profiles):
    # 0.4 against every dimension while the query is 0.5 in all of them:
    # a flat, well-understood profile.
    results = find_matches([0.5] * 10, top_k=3)
    by_closeness = sorted(results, key=lambda r: r["closeness"], reverse=True)
    assert [r["name"] for r in results] == [r["name"] for r in by_closeness]

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_reports_no_corpus_relative_fields(mock_profiles):
    r = find_matches([0.5] * 10, top_k=1)[0]
    assert "percentile" not in r
    assert "rank" not in r
    assert "total" not in r


# ── find_matches output ───────────────────────────────────────────────────────

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_attaches_ten_dimensions(mock_profiles):
    r = find_matches([0.5] * 10, top_k=1)[0]
    assert len(r["dimensions"]) == 10
    assert r["closeness"] == pytest.approx(
        sum(d["closeness"] for d in r["dimensions"]) / 10, abs=1e-3
    )
    assert r["known_dimensions"] == 10

@patch("services.matcher.get_all_profiles", return_value=MOCK_PROFILES)
def test_find_matches_can_omit_the_breakdown(mock_profiles):
    results = find_matches([0.5] * 10, top_k=2, with_breakdown=False)
    assert all("dimensions" not in r for r in results)
    assert all("closeness" in r for r in results)
