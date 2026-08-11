"""
Chat API Router
===============
Handles basic chat / Q&A endpoints that directly interact with the LLM.

Endpoints:
- POST /api/chat/send: Send a message and get a reply
- POST /api/chat/stream: (future) Stream response
"""

from fastapi import APIRouter
from app.models import ChatRequest, ChatResponse
from app.services.llm_service import get_llm_service

router = APIRouter()


@router.post("/send", response_model=ChatResponse, summary="Send a chat message")
async def chat_send(request: ChatRequest):
    """
    Send a conversation to the LLM and get a reply.
    
    - **messages**: Full conversation history (user + assistant turns)
    - **session_id**: Optional session identifier for tracking
    """
    llm_service = get_llm_service()
    
    # Convert Pydantic models to dict format for LLM service
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Call LLM
    response = llm_service.chat(messages)
    
    return ChatResponse(reply=response)


@router.get("/models", summary="List available models")
async def list_models():
    """Return current LLM provider and configured model name."""
    from app.config import settings
    return {
        "provider": settings.llm_provider,
        "current_model": settings.llm_model,
        "base_url": settings.llm_base_url,
    }