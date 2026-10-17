import json
import math
from database import get_connection

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
    mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def weighted_cosine_similarity(vec_a: list, vec_b: list, weights: list) -> float:
    w_a = [a * w for a, w in zip(vec_a, weights)]
    w_b = [b * w for b, w in zip(vec_b, weights)]
    return cosine_similarity(w_a, w_b)

def get_all_profiles() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

DEFAULT_WEIGHTS = [1.0] * 10

def find_matches(query_vector: list, top_k: int = 5, weights: list = None) -> list:
    if weights is None or len(weights) != 10:
        weights = DEFAULT_WEIGHTS
    profiles = get_all_profiles()
    results = []

    for profile in profiles:
        vector = json.loads(profile["vector"])
        confidence = json.loads(profile["confidence"])
        combined = [w * c for w, c in zip(weights, confidence)]
        weighted_query = [q * c for q, c in zip(query_vector, combined)]
        weighted_profile = [v * c for v, c in zip(vector, combined)]
        score = cosine_similarity(weighted_query, weighted_profile)
        results.append({
            "id": profile["id"],
            "name": profile["name"],
            "era": profile["era"],
            "period": profile["period"],
            "score": round(score, 4)
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]