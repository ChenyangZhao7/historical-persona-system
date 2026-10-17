import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.predictor import get_historical_responses

router = APIRouter(prefix="/predict", tags=["predict"])

class PredictRequest(BaseModel):
    question: str
    user_vector: List[float]

@router.post("/")
def predict(data: PredictRequest):
    return get_historical_responses(data.user_vector, data.question)
