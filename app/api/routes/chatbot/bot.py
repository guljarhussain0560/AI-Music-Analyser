from app.utils.chatbot.chatbot import get_ai_answer

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    question: str



@router.post("/ask", response_model=dict)
async def handle_chat(request: ChatRequest):
    """Receives a question and returns an AI-generated answer."""
    answer = await get_ai_answer(request.question)
    return {"answer": answer}