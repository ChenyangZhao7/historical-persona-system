import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Query
from database import get_connection
from services.matcher import (
    cosine_similarity,
    dimension_breakdown,
    covers_query,
    is_comparable,
    known_dimensions,
    mean_closeness,
)

router = APIRouter(prefix="/reverse", tags=["reverse"])

@router.get("/{figure_name}")
def reverse_match(
    figure_name: str,
    # negative top_k used to return len(results)-1 figures via results[:-1]
    top_k: int = Query(5, ge=1, le=50),
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
        WHERE LOWER(f.name) = LOWER(?)
    """, (figure_name,))
    
    target = cursor.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_name}' not found")

    target_vector = json.loads(target["vector"])
    target_confidence = json.loads(target["confidence"])

    cursor.execute("""
        SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
        WHERE f.id != ?
    """, (target["id"],))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        vector = json.loads(row["vector"])
        confidence = json.loads(row["confidence"])
        combined_confidence = [min(a, b) for a, b in zip(target_confidence, confidence)]
        weighted_a = [v * c for v, c in zip(target_vector, combined_confidence)]
        weighted_b = [v * c for v, c in zip(vector, combined_confidence)]
        score = cosine_similarity(weighted_a, weighted_b)
        breakdown = dimension_breakdown(
            target_vector, vector, target_confidence, confidence
        )
        if not is_comparable(breakdown) or not covers_query(breakdown, target_confidence):
            continue
        results.append({
            "id": row["id"],
            "name": row["name"],
            "era": row["era"],
            "period": row["period"],
            "score": round(score, 4),
            "closeness": mean_closeness(breakdown),
            "known_dimensions": known_dimensions(breakdown),
            "dimensions": breakdown,
        })

    results.sort(key=lambda x: x["closeness"], reverse=True)
    return {
        "query": figure_name,
        "matches": results[:top_k]
    }