import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.extractor import extract_profile
from services.matcher import find_matches

router = APIRouter(prefix="/match", tags=["match"])

class UserInput(BaseModel):
    description: str
    # negative top_k used to return len(results)-1 figures via results[:-1]
    top_k: int = Field(5, ge=1, le=50)
    weights: Optional[List[float]] = None  # 10 values, default equal weight

@router.post("/")
def match_user(data: UserInput):
    profile = extract_profile("user", data.description)
    vector = profile["vector"]
    confidence = profile["confidence"]

    # Every dimension weight would be zero, so every figure would tie at 0%.
    # Better to say why than to return five meaningless results.
    if not any(c > 0 for c in confidence):
        raise HTTPException(
            status_code=422,
            detail=(
                "That description did not contain enough behavioural signal to build "
                "a profile. Describe how you actually act in a specific situation — "
                "a conflict, a decision, a loss — rather than general traits."
            ),
        )

    matches = find_matches(
        vector, data.top_k, weights=data.weights, query_confidence=confidence
    )
    return {
        "user_profile": profile,
        "matches": matches
    }
