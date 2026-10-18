import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.wiki_fetcher import fetch_wikipedia_text
from services.extractor import extract_profile
from services.matcher import find_matches
from database import get_connection

router = APIRouter(prefix="/analyze", tags=["analyze"])

class AnalyzeRequest(BaseModel):
    name: str
    supplementary_text: str = ""  # optional extra source text

@router.post("/")
def analyze_person(data: AnalyzeRequest):
    conn = get_connection()
    cursor = conn.cursor()
    has_supplement = bool(data.supplementary_text.strip())

    cursor.execute("""
        SELECT f.id, f.name, p.vector, p.confidence, p.evidence
        FROM figures f
        JOIN profiles p ON f.id = p.figure_id
        WHERE LOWER(f.name) = LOWER(?)
    """, (data.name,))
    existing = cursor.fetchone()

    # Return cached only if no supplementary text was provided
    if existing and not has_supplement:
        profile = {
            "name": existing["name"],
            "vector": json.loads(existing["vector"]),
            "confidence": json.loads(existing["confidence"]),
            "evidence": json.loads(existing["evidence"])
        }
        matches = find_matches(profile["vector"], top_k=6, query_confidence=profile["confidence"])
        matches = [m for m in matches if m["name"].lower() != data.name.lower()]
        conn.close()
        return {"name": data.name, "profile": profile, "matches": matches[:5], "cached": True}

    # Fetch Wikipedia text
    wiki_text = fetch_wikipedia_text(data.name) or ""

    # Combine sources
    parts = []
    if wiki_text:
        parts.append(f"=== Wikipedia ===\n{wiki_text}")
    if has_supplement:
        parts.append(f"=== Supplementary Source ===\n{data.supplementary_text.strip()}")

    if not parts:
        conn.close()
        raise HTTPException(status_code=404, detail=f"No Wikipedia page found for '{data.name}' and no supplementary text provided.")

    combined_text = "\n\n".join(parts)
    profile = extract_profile(data.name, combined_text)

    if existing and has_supplement:
        # Re-analyze: update existing profile
        cursor.execute("""
            UPDATE profiles SET vector=?, confidence=?, evidence=?
            WHERE figure_id=?
        """, (
            json.dumps(profile["vector"]),
            json.dumps(profile["confidence"]),
            json.dumps(profile["evidence"]),
            existing["id"]
        ))
        conn.commit()
        conn.close()
        matches = find_matches(profile["vector"], top_k=6, query_confidence=profile["confidence"])
        matches = [m for m in matches if m["name"].lower() != data.name.lower()]
        return {"name": data.name, "profile": profile, "matches": matches[:5], "reanalyzed": True}

    # New figure: insert. era stays NULL because an on-demand lookup has no
    # reliable date — guessing 0 used to file every new figure under "ancient".
    source = "Wikipedia + Supplementary" if has_supplement else "Wikipedia"
    cursor.execute("""
        INSERT INTO figures (name, era, period, source, raw_text)
        VALUES (?, NULL, ?, ?, ?)
    """, (data.name, "unknown", source, combined_text[:4000]))

    figure_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO profiles (figure_id, vector, confidence, evidence)
        VALUES (?, ?, ?, ?)
    """, (
        figure_id,
        json.dumps(profile["vector"]),
        json.dumps(profile["confidence"]),
        json.dumps(profile["evidence"])
    ))

    conn.commit()
    conn.close()

    matches = find_matches(profile["vector"], top_k=6, query_confidence=profile["confidence"])
    matches = [m for m in matches if m["name"].lower() != data.name.lower()]
    return {"name": data.name, "profile": profile, "matches": matches[:5]}
