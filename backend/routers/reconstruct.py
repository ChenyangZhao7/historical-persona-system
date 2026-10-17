import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.reconstructor import reconstruct_history

router = APIRouter(prefix="/reconstruct", tags=["reconstruct"])

class ReconstructRequest(BaseModel):
    action: str
    source_vector: List[float]

@router.post("/")
def reconstruct(data: ReconstructRequest):
    return reconstruct_history(data.action, data.source_vector)
