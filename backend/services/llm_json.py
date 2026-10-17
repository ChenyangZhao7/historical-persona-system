"""Helpers for turning an LLM response into validated data.

The same "strip the markdown fence, json.loads, raise a 500" block used to be
copy-pasted in extractor.py, relics.py and locations.py. It lives here once now,
together with the shape checks that were missing entirely.
"""
from __future__ import annotations

import json
import re

from fastapi import HTTPException

DIMENSIONS = 10

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def strip_code_fence(text: str) -> str:
    return _FENCE.sub("", text).strip()


def parse_json_object(text: str, *, what: str) -> dict:
    """Parse a JSON object out of a model response, or fail with a 502."""
    payload = strip_code_fence(text)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"{what} did not return valid JSON: {exc}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail=f"{what} returned {type(data).__name__}, expected an object")
    return data


def parse_vector(value, *, what: str, length: int = DIMENSIONS) -> list[float]:
    """Coerce to a list of `length` numbers in [0, 1]."""
    if not isinstance(value, list) or len(value) != length:
        raise HTTPException(
            status_code=502,
            detail=f"{what} must contain {length} numbers, got {value!r}",
        )
    vector: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise HTTPException(status_code=502, detail=f"{what} contains a non-numeric value: {item!r}")
        vector.append(min(1.0, max(0.0, float(item))))
    return vector


def parse_profile(data: dict, *, name: str) -> dict:
    """Validate an extracted profile, rejecting degenerate vectors."""
    vector = parse_vector(data.get("vector"), what="vector")
    confidence = parse_vector(data.get("confidence"), what="confidence")

    if all(score == 0.0 for score in vector):
        raise HTTPException(status_code=502, detail="Model returned an all-zero vector; nothing to store")

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or len(evidence) != len(vector):
        evidence = [str(item) for item in evidence] if isinstance(evidence, list) else []
        evidence = (evidence + [""] * len(vector))[: len(vector)]

    return {
        "name": name,
        "vector": vector,
        "confidence": confidence,
        "evidence": evidence,
    }
