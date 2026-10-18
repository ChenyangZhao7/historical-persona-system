import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel, conlist
from services.reconstructor import reconstruct_history

router = APIRouter(prefix="/reconstruct", tags=["reconstruct"])

class ReconstructRequest(BaseModel):
    action: str
    # exactly ten behavioural dimensions; see routers/predict.py
    source_vector: conlist(float, min_length=10, max_length=10)

@router.post("/")
def reconstruct(data: ReconstructRequest):
    return reconstruct_history(data.action, data.source_vector)
