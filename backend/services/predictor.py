import json

from database import connection
from services.llm import complete
from services.matcher import cosine_similarity

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
            SELECT f.id, f.name, f.era, f.period, f.raw_text, p.vector
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            WHERE f.era IS NOT NULL
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _top_n_by_similarity(figures: list, user_vector: list, n: int) -> list:
    scored = []
    for fig in figures:
        vec = json.loads(fig["vector"])
        score = cosine_similarity(user_vector, vec)
        scored.append({**fig, "score": round(score, 4)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]


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


def get_historical_responses(user_vector: list, question: str) -> dict:
    all_figures = _get_all_figures_with_vectors()

    ancient = [f for f in all_figures if f["era"] is not None and f["era"] < 1800]
    modern = [f for f in all_figures if f["era"] is not None and f["era"] >= 1800]

    top_ancient = _top_n_by_similarity(ancient, user_vector, 2)
    top_modern = _top_n_by_similarity(modern, user_vector, 2)

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
            "type": fig["type"],
            "response": response_text,
        })

    return {
        "question": question,
        "figures": figures_output,
    }
