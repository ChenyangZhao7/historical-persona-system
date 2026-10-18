import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
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
    matches = find_matches(vector, data.top_k, weights=data.weights)
    return {
        "user_profile": profile,
        "matches": matches
    }
