import json

from database import connection
from services.llm import complete
from services.matcher import (
    cosine_similarity,
    compared_dimensions,
    dimension_breakdown,
    covers_query,
    is_comparable,
    known_dimensions,
    mean_closeness,
)

FIGURE_PROMPT = """You are {name}, speaking directly to someone who has asked you a question.

Known facts about your life and deeds:
{raw_text}

Your behavioural profile:
- Reaction to oppression: {d0} (0=endures silently, 1=actively resists)
- Group dependency: {d1} (0=lone wolf, 1=relies on collective)
- Principle vs interest: {d2} (0=principle above all, 1=interest above all)
- Interpersonal trust: {d3} (0=highly open, 1=deeply suspicious)
- Change orientation: {d4} (0=preserve status quo, 1=radical change)
- Emotional stability: {d5} (0=calm and controlled, 1=emotional and impulsive)
- Core motivation: {d6} (0=idealism, 1=survival/power)
- Historical mission: {d7} (0=lives in present, 1=mission-driven)
- Response to injustice: {d8} (0=accepts and adapts, 1=anger and resistance)
- Expression style: {d9} (0=silent and reserved, 1=vocal and assertive)

The question asked of you:
{question}

Respond as {name} — in the first person, in your own voice. Draw directly on your actual historical decisions, experiences, failures, and victories. Let your answer be shaped by what you genuinely lived through. Respond to the specific question with the wisdom you earned. Be direct, characterful, and unafraid. Do not break character. Do not mention similarity scores or profiles. Write 2-3 paragraphs.
"""


def _get_all_figures_with_vectors() -> list:
    """Figures that can answer a question: only those with a known era."""
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT f.id, f.name, f.era, f.period, f.raw_text, p.vector, p.confidence
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            WHERE f.era IS NOT NULL
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _score_figures(figures: list, user_vector: list, user_confidence: list = None) -> list:
    """Per-dimension agreement for every figure with a complete enough profile."""
    scored = []
    for fig in figures:
        vec = json.loads(fig["vector"])
        confidence = json.loads(fig["confidence"])
        breakdown = dimension_breakdown(
            user_vector, vec, user_confidence, confidence
        )
        if not is_comparable(breakdown) or not covers_query(breakdown, user_confidence):
            continue
        scored.append({
            **fig,
            "score": round(cosine_similarity(user_vector, vec), 4),
            "closeness": mean_closeness(breakdown),
            "known_dimensions": known_dimensions(breakdown),
            "compared_dimensions": compared_dimensions(breakdown),
            "dimensions": breakdown,
        })
    return scored


def _generate_response(figure: dict, question: str) -> str:
    safe_raw_text = (figure["raw_text"] or "").replace("{", "{{").replace("}", "}}")
    vec = json.loads(figure["vector"])
    prompt = FIGURE_PROMPT.format(
        name=figure["name"],
        raw_text=safe_raw_text,
        question=question,
        d0=vec[0], d1=vec[1], d2=vec[2],
        d3=vec[3], d4=vec[4], d5=vec[5],
        d6=vec[6], d7=vec[7], d8=vec[8], d9=vec[9],
    )
    return complete(prompt, max_tokens=800)


def get_historical_responses(
    user_vector: list, question: str, user_confidence: list = None
) -> dict:
    all_figures = _get_all_figures_with_vectors()
    scored = _score_figures(all_figures, user_vector, user_confidence)

    # Periods follow the same buckets as figures.period: ancient ends with the
    # fall of the Western Roman Empire, modern starts with the October Revolution.
    ancient = [f for f in scored if f["era"] < 476]
    modern = [f for f in scored if f["era"] >= 1917]

    top_ancient = sorted(ancient, key=lambda x: x["closeness"], reverse=True)[:2]
    top_modern = sorted(modern, key=lambda x: x["closeness"], reverse=True)[:2]

    selected = [
        {**fig, "type": "ancient"} for fig in top_ancient
    ] + [
        {**fig, "type": "modern"} for fig in top_modern
    ]

    figures_output = []
    for fig in selected:
        response_text = _generate_response(fig, question)
        figures_output.append({
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "score": fig["score"],
            "closeness": fig["closeness"],
            "known_dimensions": fig["known_dimensions"],
            "compared_dimensions": fig["compared_dimensions"],
            "dimensions": fig["dimensions"],
            "type": fig["type"],
            "response": response_text,
        })

    return {
        "question": question,
        "figures": figures_output,
    }
