import json
from database import get_connection
from services.matcher import (
    cosine_similarity,
    dimension_breakdown,
    is_comparable,
    known_dimensions,
    mean_closeness,
)

# How many neighbours the graph shows. Nodes and edges are the same set, so the
# list and the connection list always agree.
GRAPH_LIMIT = 10

def get_relationship_graph(figure_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
        WHERE f.id = ?
    """, (figure_id,))

    target = cursor.fetchone()
    if not target:
        conn.close()
        return {"error": "Figure not found"}

    cursor.execute("""
        SELECT f.id, f.name, f.era, f.period, p.vector, p.confidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
        WHERE f.id != ?
    """, (figure_id,))

    all_figures = cursor.fetchall()
    conn.close()

    target_vector = json.loads(target["vector"])
    target_confidence = json.loads(target["confidence"])

    # Rank the corpus by the same number the page prints. The old membership
    # rule was a hidden cosine cut-off at 0.95 that almost every pair cleared
    # (245 of 446 nodes) while only ten edges were ever drawn.
    scored = []
    for fig in all_figures:
        vector = json.loads(fig["vector"])
        confidence = json.loads(fig["confidence"])
        breakdown = dimension_breakdown(
            target_vector, vector, target_confidence, confidence
        )
        if not is_comparable(breakdown):
            continue
        scored.append({
            "id": fig["id"],
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "score": round(cosine_similarity(target_vector, vector), 4),
            "closeness": mean_closeness(breakdown),
            "known_dimensions": known_dimensions(breakdown),
        })
    scored.sort(key=lambda x: x["closeness"], reverse=True)
    scored = scored[:GRAPH_LIMIT]

    target_name = target["name"]
    nodes = [{"id": target["id"], "name": target_name, "era": target["era"], "type": "target"}]
    edges = []
    id_to_name = {target["id"]: target_name}

    for fig in scored:
        id_to_name[fig["id"]] = fig["name"]
        nodes.append({
            "id": fig["id"],
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "type": "related",
            "similarity": fig["score"],
            "closeness": fig["closeness"],
            "known_dimensions": fig["known_dimensions"],
        })
        edges.append({
            "source": target["id"],
            "target": fig["id"],
            "source_name": target_name,
            "target_name": fig["name"],
            "weight": fig["score"],
            "closeness": fig["closeness"],
            "type": "similarity"
        })

    return {
        "center": target_name,
        "nodes": nodes,
        "edges": edges
    }