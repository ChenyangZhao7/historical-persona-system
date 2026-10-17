import json
import pytest
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


VALID_PROFILE = {
    "name": "Test Figure",
    "vector": [0.8, 0.5, 0.6, 0.7, 0.7, 0.4, 0.7, 0.9, 0.7, 0.6],
    "confidence": [0.9, 0.8, 0.7, 0.8, 0.9, 0.7, 0.8, 0.9, 0.8, 0.7],
    "evidence": [f"Evidence {i}" for i in range(10)],
}


@patch("services.extractor.complete")
def test_extract_profile_returns_valid_structure(mock_complete):
    mock_complete.return_value = json.dumps(VALID_PROFILE)

    from services.extractor import extract_profile
    result = extract_profile("Test Figure", "Some text about Test Figure.")

    assert "vector" in result
    assert "confidence" in result
    assert "evidence" in result
    assert len(result["vector"]) == 10
    assert len(result["confidence"]) == 10
    assert len(result["evidence"]) == 10


@patch("services.extractor.complete")
def test_extract_profile_name_overrides_model_name(mock_complete):
    profile = {**VALID_PROFILE, "name": "Wrong Name From Model"}
    mock_complete.return_value = json.dumps(profile)

    from services.extractor import extract_profile
    result = extract_profile("Correct Name", "Some text.")
    assert result["name"] == "Correct Name"


@patch("services.extractor.complete")
def test_extract_profile_strips_markdown_fences(mock_complete):
    mock_complete.return_value = f"```json\n{json.dumps(VALID_PROFILE)}\n```"

    from services.extractor import extract_profile
    result = extract_profile("Test Figure", "Some text.")
    assert result["vector"] == VALID_PROFILE["vector"]


@patch("services.extractor.complete")
def test_extract_profile_raises_on_invalid_json(mock_complete):
    from fastapi import HTTPException

    mock_complete.return_value = "not valid json at all"

    from services.extractor import extract_profile
    with pytest.raises(HTTPException) as exc_info:
        extract_profile("Test Figure", "Some text.")
    assert exc_info.value.status_code == 502


@patch("services.extractor.complete")
def test_extract_profile_rejects_degenerate_vector(mock_complete):
    from fastapi import HTTPException

    mock_complete.return_value = json.dumps(
        {**VALID_PROFILE, "vector": [0.0] * 10, "confidence": [0.0] * 10}
    )

    from services.extractor import extract_profile
    with pytest.raises(HTTPException) as exc_info:
        extract_profile("Test Figure", "Some text.")
    assert exc_info.value.status_code == 502


@patch("services.extractor.complete")
def test_extract_profile_vector_values_in_range(mock_complete):
    mock_complete.return_value = json.dumps(VALID_PROFILE)

    from services.extractor import extract_profile
    result = extract_profile("Test Figure", "Some text.")
    for v in result["vector"]:
        assert 0.0 <= v <= 1.0


def test_extract_profile_rejects_empty_text():
    from fastapi import HTTPException

    from services.extractor import extract_profile
    with pytest.raises(HTTPException) as exc_info:
        extract_profile("Test Figure", "   ")
    assert exc_info.value.status_code == 400
