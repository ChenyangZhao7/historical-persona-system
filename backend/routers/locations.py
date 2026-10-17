import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from locations import get_figure_locations
from services.figure_resolver import resolve_figure

router = APIRouter(prefix="/locations", tags=["locations"])

class LocationRequest(BaseModel):
    name: str

@router.post("/")
def locations(data: LocationRequest):
    figure = resolve_figure(data.name)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{data.name}' not found")
    return get_figure_locations(figure["id"])
