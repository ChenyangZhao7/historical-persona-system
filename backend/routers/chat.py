import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel
from services.persona_chat import persona_chat

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    name: str
    message: str

@router.post("/")
def chat(data: ChatRequest):
    return persona_chat(data.name, data.message)
