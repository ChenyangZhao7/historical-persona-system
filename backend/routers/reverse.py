import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from database import get_connection
from services.matcher import cosine_similarity

router = APIRouter(prefix="/reverse", tags=["reverse"])

@router.get("/{figure_name}")
def reverse_match(figure_name: str, top_k: int = 5):
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
        results.append({
            "id": row["id"],
            "name": row["name"],
            "era": row["era"],
            "period": row["period"],
            "score": round(score, 4)
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": figure_name,
        "matches": results[:top_k]
    }