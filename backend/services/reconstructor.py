import json

from database import connection
from services.llm import complete
from services.matcher import cosine_similarity

RECONSTRUCT_PROMPT = """You are a historian writing a passage for an academic history book.

You have been asked to write a plausible historical narrative: what would {name} have done if they had faced a situation equivalent to the following modern action?

Modern action to adapt:
{action}

Known historical facts about {name}:
{raw_text}

Era context: {name} lived around {era_label}, in {civilization}. Consider the specific geography, social structure, gender roles, religious frameworks, political systems, and daily life constraints of that world. Do not apply modern frameworks.

Civilisation details:
- Region/geography: {region}
- Social structure: {social_structure}
- Gender context: {gender_context}

Behavioural profile of {name} (10 dimensions, 0.0–1.0):
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

Write a plausible historical narrative, in the style of a history book passage, describing what {name} would have done in an equivalent situation within their own time and place. Adapt the core dynamics of the modern action — its stakes, relationships, choices — into the actual world {name} inhabited. Write 2-3 paragraphs. Ground every inference in the behavioural profile and known facts. Begin the passage with the label: [FABRICATED HISTORY — {name}]
"""


def _era_context(era: int) -> dict:
    if era < -500:
        return {
            "era_label": f"{abs(era)} BC",
            "civilization": "an ancient civilisation shaped by oral tradition, divine kingship, and city-states",
            "region": "the ancient Near East, Mediterranean, or river valley civilisations",
            "social_structure": "rigid hierarchies of priests, warriors, and peasants under a monarch or council",
            "gender_context": "a world where gender roles were strictly enforced by custom, religion, and law",
        }
    elif era < 500:
        return {
            "era_label": f"{abs(era)} BC/AD",
            "civilization": "the classical world of emerging empires, philosophy, and expanding trade networks",
            "region": "the Mediterranean basin, Persia, China, or the Indian subcontinent",
            "social_structure": "a society of citizen-soldiers, slaves, merchants, and aristocrats under republic or empire",
            "gender_context": "a world where women's public roles were heavily circumscribed except in specific religious or royal contexts",
        }
    elif era < 1500:
        return {
            "era_label": f"{era} AD",
            "civilization": "the medieval world shaped by religious authority, feudal obligation, and limited literacy",
            "region": "medieval Europe, the Islamic world, sub-Saharan Africa, or dynastic East Asia",
            "social_structure": "a feudal or theocratic order of lords, clergy, artisans, and serfs",
            "gender_context": "a world where gender determined almost every aspect of public, legal, and domestic life",
        }
    else:
        return {
            "era_label": f"{era} AD",
            "civilization": "the early modern world of print culture, nation-states, and emerging industrial change",
            "region": "early modern Europe, the Ottoman Empire, Mughal India, or the Americas",
            "social_structure": "a society in transition, with merchant classes, colonial structures, and religious reform movements",
            "gender_context": "a world where gender norms were being contested but still profoundly constrained public life",
        }


def _get_ancient_figures_with_vectors() -> list:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT f.id, f.name, f.era, f.period, f.raw_text, p.vector
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            WHERE f.era IS NOT NULL AND f.era < 1800
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _top_n_by_similarity(figures: list, source_vector: list, n: int) -> list:
    scored = []
    for fig in figures:
        vec = json.loads(fig["vector"])
        score = cosine_similarity(source_vector, vec)
        scored.append({**fig, "score": round(score, 4)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]


def _generate_narrative(figure: dict, action: str) -> str:
    safe_raw_text = (figure["raw_text"] or "").replace("{", "{{").replace("}", "}}")
    vec = json.loads(figure["vector"])
    ctx = _era_context(figure["era"])
    prompt = RECONSTRUCT_PROMPT.format(
        name=figure["name"],
        action=action,
        raw_text=safe_raw_text,
        era_label=ctx["era_label"],
        civilization=ctx["civilization"],
        region=ctx["region"],
        social_structure=ctx["social_structure"],
        gender_context=ctx["gender_context"],
        d0=vec[0], d1=vec[1], d2=vec[2],
        d3=vec[3], d4=vec[4], d5=vec[5],
        d6=vec[6], d7=vec[7], d8=vec[8], d9=vec[9],
    )
    return complete(prompt, max_tokens=900)


def reconstruct_history(action: str, source_vector: list) -> dict:
    ancient_figures = _get_ancient_figures_with_vectors()
    top_3 = _top_n_by_similarity(ancient_figures, source_vector, 3)

    figures_output = []
    for fig in top_3:
        narrative = _generate_narrative(fig, action)
        figures_output.append({
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "score": fig["score"],
            "narrative": narrative,
        })

    return {
        "action": action,
        "figures": figures_output,
    }
