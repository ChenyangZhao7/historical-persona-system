import json
import math

from database import get_connection

# Canonical dimension order. Mirrors services/extractor.DIMENSIONS and the
# DIMS array on the frontend.
DIMENSIONS = [
    "reaction_to_oppression",
    "group_dependency",
    "principle_vs_interest",
    "interpersonal_trust",
    "change_orientation",
    "emotional_stability",
    "core_motivation",
    "historical_mission",
    "response_to_injustice",
    "expression_style",
]


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    # zip() silently truncates to the shorter vector, which turned a
    # three-value query into a ranking on three dimensions. Fail loudly.
    if len(vec_a) != len(vec_b):
        raise ValueError(
            f"vectors must have the same length ({len(vec_a)} != {len(vec_b)})"
        )
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
    mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def weighted_cosine_similarity(vec_a: list, vec_b: list, weights: list) -> float:
    if not (len(vec_a) == len(vec_b) == len(weights)):
        raise ValueError(
            f"vectors and weights must share a length ({len(vec_a)}, {len(vec_b)}, {len(weights)})"
        )
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


def dimension_breakdown(
    query_vector: list,
    figure_vector: list,
    query_confidence: list = None,
    figure_confidence: list = None,
) -> list:
    """Compare two profiles dimension by dimension.

    `closeness` is ``1 - |difference|`` on that dimension: 1.0 means the two
    profiles agree completely, 0.0 means they sit at opposite ends of the
    scale. Both raw values are returned unchanged so the direction of a
    mismatch stays visible, and each figure's `confidence` is passed through
    because several dimensions are inferred from indirect evidence.
    """
    breakdown = []
    for i, name in enumerate(DIMENSIONS):
        q = query_vector[i] if i < len(query_vector) else 0.0
        f = figure_vector[i] if i < len(figure_vector) else 0.0
        breakdown.append({
            "dimension": name,
            "query": round(q, 3),
            "figure": round(f, 3),
            "gap": round(abs(q - f), 3),
            "closeness": round(max(0.0, 1.0 - abs(q - f)), 3),
            "query_confidence": (
                round(query_confidence[i], 3)
                if query_confidence and i < len(query_confidence) else None
            ),
            "figure_confidence": (
                round(figure_confidence[i], 3)
                if figure_confidence and i < len(figure_confidence) else None
            ),
        })
    return breakdown


def mean_closeness(breakdown: list, weights: list = None) -> float:
    """Weighted average agreement across the ten dimensions.

    Each dimension contributes
    ``closeness * user_weight * query_confidence * figure_confidence``.
    A dimension only counts when *both* sides have evidence for it: the
    figure's profile may not cover it, and the user's description may not have
    mentioned it. Treating an unmentioned user dimension as a real 0.5 made a
    short description measure "which figure is most average" rather than
    "which figure resembles me". `weights` is the Match page's preset / slider
    vector: raising a dimension makes it matter more to the score.
    """
    weighted = 0.0
    total_weight = 0.0
    for i, d in enumerate(breakdown):
        user_weight = weights[i] if weights else 1.0
        figure_conf = d["figure_confidence"]
        if figure_conf is None:
            figure_conf = 1.0
        query_conf = d["query_confidence"]
        if query_conf is None:
            query_conf = 1.0
        weight = user_weight * figure_conf * query_conf
        weighted += d["closeness"] * weight
        total_weight += weight
    if total_weight == 0:
        # Everything weighted to zero is a degenerate request; fall back to the
        # unweighted average rather than reporting a meaningless 0.
        return 0.0 if weights is None else mean_closeness(breakdown)
    return round(weighted / total_weight, 4)


def compared_dimensions(breakdown: list) -> int:
    """Dimensions carrying evidence on both sides — what the score rests on."""
    return sum(
        1 for d in breakdown
        if (d["figure_confidence"] is None or d["figure_confidence"] > 0)
        and (d["query_confidence"] is None or d["query_confidence"] > 0)
    )


# A score built on two dimensions and a score built on eight are not
# comparable: the thin one has far more room to look good by accident. A
# candidate may miss one of the traits the caller described, but not a third of
# them.
COVERAGE_SHARE = 0.8


def covers_query(breakdown: list, query_confidence: list = None) -> bool:
    """Whether this candidate can be compared on most of what was described."""
    if not query_confidence:
        return True
    described = sum(1 for c in query_confidence if c and c > 0)
    if described == 0:
        return False
    required = max(1, round(described * COVERAGE_SHARE))
    return compared_dimensions(breakdown) >= required


def known_dimensions(breakdown: list) -> int:
    """How many of the ten dimensions the figure's profile actually covers."""
    return sum(
        1 for d in breakdown
        if d["figure_confidence"] is None or d["figure_confidence"] > 0
    )


# A "how similar is this person to you" claim needs evidence on most of the ten
# dimensions to mean anything. Five figures in the corpus fall short today
# (Newton 2/10, Daguerre / Edison / Gagarin 3/10, Meiji 4/10); ranking them
# alongside complete profiles would let a mostly-empty profile take first place.
# They stay in the database and on the Database page — they are simply not
# offered as behaviour matches until their profiles are filled in.
MIN_KNOWN_DIMENSIONS = 6


def is_comparable(breakdown: list) -> bool:
    """Whether a profile covers enough dimensions to be compared fairly."""
    return known_dimensions(breakdown) >= MIN_KNOWN_DIMENSIONS


DEFAULT_WEIGHTS = [1.0] * 10

def find_matches(
    query_vector: list,
    top_k: int = 5,
    weights: list = None,
    with_breakdown: bool = True,
    query_confidence: list = None,
) -> list:
    """Figures ordered by how closely their profile matches `query_vector`.

    Ordering is by `closeness`, which is the number the interface prints, so
    the list order always agrees with the figures shown next to it. Cosine over
    uncentred 0..1 vectors clusters near 0.95 for almost every pair, so it is
    carried in the payload for diagnostics only and never displayed.

    `query_confidence` is the caller's own per-dimension confidence. Without
    it, dimensions the caller never described would be scored as if they were
    real values.
    """
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
        breakdown = dimension_breakdown(
            query_vector, vector, query_confidence, confidence
        )
        if not is_comparable(breakdown) or not covers_query(breakdown, query_confidence):
            continue
        results.append({
            "id": profile["id"],
            "name": profile["name"],
            "era": profile["era"],
            "period": profile["period"],
            "score": round(score, 4),
            "closeness": mean_closeness(breakdown, weights),
            "known_dimensions": known_dimensions(breakdown),
            "compared_dimensions": compared_dimensions(breakdown),
            "_breakdown": breakdown,
        })

    results.sort(key=lambda x: x["closeness"], reverse=True)

    top = results[:top_k]
    for entry in top:
        breakdown = entry.pop("_breakdown")
        if with_breakdown:
            entry["dimensions"] = breakdown
    return top