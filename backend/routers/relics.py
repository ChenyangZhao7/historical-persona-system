import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel
from relics import match_relic

router = APIRouter(prefix="/relics", tags=["relics"])

class RelicRequest(BaseModel):
    description: str
    material: str

@router.post("/match/")
def relic_match(data: RelicRequest):
    return match_relic(data.description, data.material)
