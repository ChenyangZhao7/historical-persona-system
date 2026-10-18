import json

from fastapi import HTTPException

from database import connection
from services.llm import complete
from services.llm_json import parse_json_object, parse_vector
from services.matcher import (
    cosine_similarity,
    dimension_breakdown,
    is_comparable,
    known_dimensions,
    mean_closeness,
)

RELICS_PROMPT = """You are a museum curator and behavioural analyst.

A relic has been found with the following description:
Material: {material}
Description: {description}

Based on this relic, extract behavioural signals about its likely owner or creator:
- Would they be a lone wolf or group-oriented?
- Would they be change-oriented or tradition-preserving?
- Would they be mission-driven or present-focused?
- Would they be assertive or reserved in expression?

Return ONLY valid JSON:
{{
  "inferred_vector": [d0, d1, d2, d3, d4, d5, d6, d7, d8, d9],
  "confidence": [c0, c1, c2, c3, c4, c5, c6, c7, c8, c9],
  "reasoning": "brief explanation"
}}

Scores are 0.0 to 1.0. Set confidence to 0 if no evidence.
"""

def match_relic(description: str, material: str) -> dict:
    prompt = RELICS_PROMPT.format(description=description, material=material)

    raw = complete(prompt, max_tokens=500)
    relic_profile = parse_json_object(raw, what="Relic analysis")
    relic_vector = parse_vector(relic_profile.get("inferred_vector"), what="relic vector")
    relic_profile["inferred_vector"] = relic_vector

    with connection() as conn:
        figures = conn.execute(
            """
            SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            """
        ).fetchall()

    relic_confidence = relic_profile.get("confidence")
    results = []
    for fig in figures:
        vector = json.loads(fig["vector"])
        confidence = json.loads(fig["confidence"])
        score = cosine_similarity(relic_vector, vector)
        breakdown = dimension_breakdown(
            relic_vector, vector, relic_confidence, confidence
        )
        if not is_comparable(breakdown):
            continue
        results.append({
            "id": fig["id"],
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "score": round(score, 4),
            "closeness": mean_closeness(breakdown),
            "known_dimensions": known_dimensions(breakdown),
            "dimensions": breakdown,
        })

    results.sort(key=lambda x: x["closeness"], reverse=True)

    return {
        "relic_profile": relic_profile,
        "matches": results[:5]
    }
