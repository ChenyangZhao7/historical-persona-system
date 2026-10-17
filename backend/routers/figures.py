import json

from fastapi import APIRouter
from pydantic import BaseModel

from database import connection
from services.extractor import extract_profile

router = APIRouter(prefix="/figures", tags=["figures"])


class FigureCreate(BaseModel):
    name: str
    era: int | None = None
    period: str = "unknown"
    source: str = "manual"
    raw_text: str


@router.post("/")
def create_figure(data: FigureCreate):
    profile = extract_profile(data.name, data.raw_text)

    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO figures (name, era, period, source, raw_text) VALUES (?, ?, ?, ?, ?)",
            (data.name, data.era, data.period, data.source, data.raw_text),
        )
        figure_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO profiles (figure_id, vector, confidence, evidence) VALUES (?, ?, ?, ?)",
            (
                figure_id,
                json.dumps(profile["vector"]),
                json.dumps(profile["confidence"]),
                json.dumps(profile["evidence"]),
            ),
        )

    return {"id": figure_id, "name": data.name, "profile": profile}


@router.get("/")
def list_figures(evidence: bool = True):
    """All figures with their vectors.

    `evidence=false` drops the ~770 KB of per-dimension reasoning that the map
    and benchmark pages never display (0.85 MB -> ~90 KB).
    """
    columns = "p.vector, p.confidence" if not evidence else "p.vector, p.confidence, p.evidence"

    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT f.id, f.name, f.era, f.period, {columns}
            FROM figures f
            JOIN profiles p ON p.figure_id = f.id
            ORDER BY f.name ASC
            """
        ).fetchall()

    figures = []
    for row in rows:
        item = {
            "id": row["id"],
            "name": row["name"],
            "era": row["era"],
            "period": row["period"],
            "vector": json.loads(row["vector"]),
            "confidence": json.loads(row["confidence"]),
        }
        if evidence:
            item["evidence"] = json.loads(row["evidence"])
        figures.append(item)
    return figures
