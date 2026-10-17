"""Tests for the LLM-output validation helpers.

These do not touch the network or the database; they cover the shape checks
that used to be missing entirely (a malformed model response used to be stored
as a zero vector and quietly poisoned every match).
"""
import sys
import os

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_json import parse_json_object, parse_profile, parse_vector


class TestParseJsonObject:
    def test_plain_object(self):
        assert parse_json_object('{"a": 1}', what="test") == {"a": 1}

    def test_strips_json_fence(self):
        assert parse_json_object('```json\n{"a": 1}\n```', what="test") == {"a": 1}

    def test_strips_bare_fence(self):
        assert parse_json_object("```\n{\"a\": 1}\n```", what="test") == {"a": 1}

    def test_rejects_garbage(self):
        with pytest.raises(HTTPException) as exc:
            parse_json_object("I cannot help with that", what="test")
        assert exc.value.status_code == 502

    def test_rejects_array(self):
        with pytest.raises(HTTPException):
            parse_json_object("[1, 2, 3]", what="test")


class TestParseVector:
    def test_accepts_ten_numbers(self):
        assert len(parse_vector([0.5] * 10, what="v")) == 10

    def test_clamps_out_of_range(self):
        assert parse_vector([-1, 2] + [0.5] * 8, what="v")[:2] == [0.0, 1.0]

    def test_rejects_wrong_length(self):
        with pytest.raises(HTTPException):
            parse_vector([0.5] * 9, what="v")

    def test_rejects_non_numeric(self):
        with pytest.raises(HTTPException):
            parse_vector([0.5] * 9 + ["x"], what="v")

    def test_rejects_bools(self):
        with pytest.raises(HTTPException):
            parse_vector([True] * 10, what="v")


class TestParseProfile:
    def test_pads_short_evidence(self):
        result = parse_profile(
            {"vector": [0.2] * 10, "confidence": [0.9] * 10, "evidence": ["only one"]},
            name="Caesar",
        )
        assert result["name"] == "Caesar"
        assert len(result["evidence"]) == 10
        assert result["evidence"][0] == "only one"

    def test_rejects_degenerate_vector(self):
        with pytest.raises(HTTPException) as exc:
            parse_profile({"vector": [0.0] * 10, "confidence": [0.5] * 10}, name="Nobody")
        assert exc.value.status_code == 502
