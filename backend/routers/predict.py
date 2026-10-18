import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel, conlist
from typing import Optional
from services.predictor import get_historical_responses

router = APIRouter(prefix="/predict", tags=["predict"])

class PredictRequest(BaseModel):
    question: str
    # exactly ten behavioural dimensions; a shorter vector would be silently
    # truncated by cosine_similarity and rank the whole corpus on a subset.
    user_vector: conlist(float, min_length=10, max_length=10)
    # Which dimensions the profile's description actually supported. Optional
    # for older saved profiles; without it, unmentioned dimensions are scored
    # as if they were real values.
    user_confidence: Optional[conlist(float, min_length=10, max_length=10)] = None

@router.post("/")
def predict(data: PredictRequest):
    return get_historical_responses(
        data.user_vector, data.question, data.user_confidence
    )
