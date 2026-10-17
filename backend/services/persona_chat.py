import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException

from services.llm import complete
from services.figure_resolver import resolve_figure
from imputer import impute_profile

CHAT_PROMPT = """You are {name}, the historical figure who lived around {era}.

Your behavioural profile (some dimensions inferred from similar figures):
- Reaction to oppression: {d0}
- Group dependency: {d1}
- Principle vs interest: {d2}
- Interpersonal trust: {d3}
- Change orientation: {d4}
- Emotional stability: {d5}
- Core motivation: {d6}
- Historical mission: {d7}
- Response to injustice: {d8}
- Expression style: {d9}

Known facts about you:
{raw_text}

Respond as {name} would, staying true to your behavioural profile and historical context.
Speak in first person. Be concise but characterful.
Do not break character. Do not mention your behavioural scores.
"""

def persona_chat(name: str, message: str) -> dict:
    figure = resolve_figure(name)

    if not figure:
        raise HTTPException(status_code=404, detail=f"Could not find or fetch data for '{name}'")

    imputed = impute_profile(figure["id"])
    if "error" in imputed:
        raise HTTPException(status_code=500, detail=f"Could not build profile for '{name}'")
    vector = imputed["imputed_vector"]

    safe_raw_text = (figure["raw_text"] or "").replace("{", "{{").replace("}", "}}")
    system_prompt = CHAT_PROMPT.format(
        name=figure["name"],
        era=figure["era"],
        raw_text=safe_raw_text,
        d0=vector[0], d1=vector[1], d2=vector[2],
        d3=vector[3], d4=vector[4], d5=vector[5],
        d6=vector[6], d7=vector[7], d8=vector[8], d9=vector[9]
    )

    response_text = complete(message, system=system_prompt, max_tokens=500)

    return {
        "figure": figure["name"],
        "message": message,
        "response": response_text
    }
