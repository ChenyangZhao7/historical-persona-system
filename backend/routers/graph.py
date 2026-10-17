import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.graph import get_relationship_graph
from services.figure_resolver import resolve_figure

router = APIRouter(prefix="/graph", tags=["graph"])

class GraphRequest(BaseModel):
    name: str

@router.post("/")
def graph(data: GraphRequest):
    figure = resolve_figure(data.name)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{data.name}' not found")
    result = get_relationship_graph(figure["id"])
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
