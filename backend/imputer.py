import json

from database import connection
from services.matcher import cosine_similarity

LOW_CONFIDENCE = 0.4      # below this a dimension is considered missing
DONOR_CONFIDENCE = 0.6    # a donor figure must know the dimension this well
SHARED_CONFIDENCE = 0.5   # dimensions used to judge donor similarity
MIN_SHARED_DIMS = 3       # need this many shared dimensions to trust a donor


def impute_profile(figure_id: int, user_vector: list | None = None) -> dict:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT f.id, f.name, f.era, p.vector, p.confidence
            FROM figures f
            JOIN profiles p ON f.id = p.figure_id
            WHERE f.id = ?
            """,
            (figure_id,),
        )
        target = cursor.fetchone()
        if not target:
            return {"error": "Figure not found"}

        cursor.execute(
            """
            SELECT f.id, f.name, f.era, p.vector, p.confidence
            FROM figures f
            JOIN profiles p ON f.id = p.figure_id
            WHERE f.id != ?
            """,
            (figure_id,),
        )
        donors = cursor.fetchall()

    target_vector = json.loads(target["vector"])
    target_confidence = json.loads(target["confidence"])

    imputed_vector = target_vector.copy()
    imputed_from = {}

    for i in range(10):
        if target_confidence[i] < LOW_CONFIDENCE:
            best_score = -1
            best_figure = None
            best_value = None

            # borrow this dimension from the most similar figure that knows it
            for fig in donors:
                fig_vector = json.loads(fig["vector"])
                fig_confidence = json.loads(fig["confidence"])

                if fig_confidence[i] >= DONOR_CONFIDENCE:
                    known_dims = [j for j in range(10)
                                  if target_confidence[j] >= SHARED_CONFIDENCE and fig_confidence[j] >= SHARED_CONFIDENCE]

                    if len(known_dims) >= MIN_SHARED_DIMS:
                        sim = cosine_similarity(
                            [target_vector[j] for j in known_dims],
                            [fig_vector[j] for j in known_dims]
                        )
                        if sim > best_score:
                            best_score = sim
                            best_figure = fig["name"]
                            best_value = fig_vector[i]

            # the caller's own vector can also donate (e.g. /chat with a user profile)
            if user_vector is not None:
                known_dims = [j for j in range(10) if target_confidence[j] >= SHARED_CONFIDENCE]
                if len(known_dims) >= MIN_SHARED_DIMS:
                    sim = cosine_similarity(
                        [target_vector[j] for j in known_dims],
                        [user_vector[j] for j in known_dims]
                    )
                    if sim > best_score:
                        best_score = sim
                        best_figure = "user"
                        best_value = user_vector[i]

            if best_figure:
                imputed_vector[i] = best_value
                imputed_from[i] = {
                    "borrowed_from": best_figure,
                    "similarity": round(best_score, 3)
                }

    return {
        "figure_id": figure_id,
        "original_vector": target_vector,
        "original_confidence": target_confidence,
        "imputed_vector": imputed_vector,
        "imputed_from": imputed_from
    }
