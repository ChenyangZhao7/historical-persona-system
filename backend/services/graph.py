import json
from database import get_connection
from services.matcher import cosine_similarity

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
    
    target_name = target["name"]
    nodes = [{"id": target["id"], "name": target_name, "era": target["era"], "type": "target"}]
    edges = []
    id_to_name = {target["id"]: target_name}

    for fig in all_figures:
        vector = json.loads(fig["vector"])
        score = cosine_similarity(target_vector, vector)

        if score > 0.95:
            id_to_name[fig["id"]] = fig["name"]
            nodes.append({
                "id": fig["id"],
                "name": fig["name"],
                "era": fig["era"],
                "period": fig["period"],
                "type": "related",
                "similarity": round(score, 4)
            })
            edges.append({
                "source": target["id"],
                "target": fig["id"],
                "source_name": target_name,
                "target_name": fig["name"],
                "weight": round(score, 4),
                "type": "similarity"
            })

    edges.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "center": target_name,
        "nodes": nodes,
        "edges": edges[:10]
    }