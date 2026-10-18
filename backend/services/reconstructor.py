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


def _era_label(era: int) -> str:
    return f"{abs(era)} BC" if era < 0 else f"{era} AD"


def _era_context(era: int) -> dict:
    """Material world for the five periods stored in figures.period."""
    label = _era_label(era)

    if era < 476:
        return {
            "era_label": label,
            "civilization": "an ancient civilisation shaped by oral tradition, divine kingship, and city-states",
            "region": "the ancient Near East, Mediterranean, or river valley civilisations",
            "social_structure": "rigid hierarchies of priests, warriors, and peasants under a monarch or council",
            "gender_context": "a world where gender roles were strictly enforced by custom, religion, and law",
        }
    elif era < 1500:
        return {
            "era_label": label,
            "civilization": "the medieval world shaped by religious authority, feudal obligation, and limited literacy",
            "region": "medieval Europe, the Islamic world, sub-Saharan Africa, or dynastic East Asia",
            "social_structure": "a feudal or theocratic order of lords, clergy, artisans, and serfs",
            "gender_context": "a world where gender determined almost every aspect of public, legal, and domestic life",
        }
    elif era < 1917:
        return {
            "era_label": label,
            "civilization": "the early modern and industrial world of print culture, nation-states, and mechanised production",
            "region": "early modern and industrial Europe, the Ottoman Empire, Mughal India, Qing China, or the Americas",
            "social_structure": "a society in transition, with merchant and industrial classes, colonial structures, and reforming states",
            "gender_context": "a world where gender norms were contested but still profoundly constrained public life",
        }
    elif era < 1945:
        return {
            "era_label": label,
            "civilization": "the industrial and interwar world of mass politics, total war, and ideological conflict",
            "region": "an industrialised and imperial world order, from Europe and North America to colonial Asia and Africa",
            "social_structure": "a society of mass parties, industrial labour, colonial administration, and expanding state power",
            "gender_context": "a world where women's suffrage and wartime labour were beginning to reshape public roles",
        }
    return {
        "era_label": label,
        "civilization": "the contemporary world of decolonisation, cold-war rivalry, digital technology, and globalisation",
        "region": "a globally connected world of nation-states, international institutions, and urban economies",
        "social_structure": "a society of mass education, service economies, global supply chains, and contested welfare states",
        "gender_context": "a world where gender roles were formally equal in law but still uneven in practice",
    }


def _get_ancient_figures_with_vectors() -> list:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT f.id, f.name, f.era, f.period, f.raw_text, p.vector, p.confidence
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            WHERE f.era IS NOT NULL AND f.era < 476
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _score_figures(figures: list, source_vector: list, source_confidence: list = None) -> list:
    """Per-dimension agreement for every figure with a complete enough profile."""
    scored = []
    for fig in figures:
        vec = json.loads(fig["vector"])
        confidence = json.loads(fig["confidence"])
        breakdown = dimension_breakdown(
            source_vector, vec, source_confidence, confidence
        )
        if not is_comparable(breakdown) or not covers_query(breakdown, source_confidence):
            continue
        scored.append({
            **fig,
            "score": round(cosine_similarity(source_vector, vec), 4),
            "closeness": mean_closeness(breakdown),
            "known_dimensions": known_dimensions(breakdown),
            "compared_dimensions": compared_dimensions(breakdown),
            "dimensions": breakdown,
        })
    return scored


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


def reconstruct_history(
    action: str, source_vector: list, source_confidence: list = None
) -> dict:
    ancient_figures = _get_ancient_figures_with_vectors()
    scored = _score_figures(ancient_figures, source_vector, source_confidence)
    top_3 = sorted(scored, key=lambda x: x["closeness"], reverse=True)[:3]

    figures_output = []
    for fig in top_3:
        narrative = _generate_narrative(fig, action)
        figures_output.append({
            "name": fig["name"],
            "era": fig["era"],
            "period": fig["period"],
            "score": fig["score"],
            "closeness": fig["closeness"],
            "known_dimensions": fig["known_dimensions"],
            "compared_dimensions": fig["compared_dimensions"],
            "dimensions": fig["dimensions"],
            "narrative": narrative,
        })

    return {
        "action": action,
        "figures": figures_output,
    }
