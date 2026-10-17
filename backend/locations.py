from fastapi import HTTPException

from database import connection
from services.llm import complete
from services.llm_json import parse_json_object

LOCATIONS_PROMPT = """You are a historical geographer. Based on the following information about {name} (era: {era}), list the key locations associated with their life.

Known facts:
{raw_text}

Return ONLY valid JSON, no other text:
{{
  "locations": [
    {{
      "name": "location name",
      "lat": latitude as float,
      "lng": longitude as float,
      "description": "why this place matters to {name}",
      "type": "birthplace/battlefield/capital/exile/death"
    }}
  ]
}}

Include 3-6 locations maximum. Only include locations with high historical confidence.
"""

def get_figure_locations(figure_id: int) -> dict:
    with connection() as conn:
        figure = conn.execute(
            "SELECT f.name, f.era, f.raw_text FROM figures f WHERE f.id = ?",
            (figure_id,),
        ).fetchone()

    if not figure:
        return {"error": "Figure not found"}

    safe_raw_text = (figure["raw_text"] or "").replace("{", "{{").replace("}", "}}")
    prompt = LOCATIONS_PROMPT.format(
        name=figure["name"],
        era=figure["era"],
        raw_text=safe_raw_text
    )

    raw = complete(prompt, max_tokens=1000)
    result = parse_json_object(raw, what="Location listing")
    if not isinstance(result.get("locations"), list):
        raise HTTPException(status_code=502, detail="Location listing returned no locations array")

    return {
        "figure": figure["name"],
        "era": figure["era"],
        "locations": result["locations"]
    }
