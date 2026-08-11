"""
Admin API Router
================
Administrative endpoints for system management.

Endpoints:
- GET /api/admin/stats: System statistics
- POST /api/admin/clear-kb: Clear entire knowledge base (use with caution)
- GET /api/admin/health: Health check with details
"""

from fastapi import APIRouter, HTTPException
from app.models import KBStats
from app.services.rag_service import get_rag_service
from app.services.llm_service import get_llm_service
from app.config import settings

router = APIRouter()


@router.get("/stats", response_model=KBStats, summary="Knowledge base statistics")
async def get_stats():
    """Get knowledge base statistics including document count and chunk count."""
    rag_service = get_rag_service()
    stats = rag_service.get_knowledge_base_status()
    return KBStats(**stats)


@router.get("/health", summary="Detailed health check")
async def health_check():
    """
    Detailed health check endpoint that verifies:
    - LLM connectivity
    - Vector DB status
    - File storage
    """
    rag_service = get_rag_service()
    
    # Check vector DB
    try:
        stats = rag_service.get_knowledge_base_status()
        vector_db_status = "ok"
    except Exception as e:
        vector_db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
        },
        "vector_db": {
            "status": vector_db_status,
            "collection": settings.chroma_collection_name,
        },
        "storage": {
            "upload_dir": settings.upload_dir,
        },
    }


@router.post("/clear-kb", summary="Clear entire knowledge base")
async def clear_knowledge_base():
    """
    Clear ALL data from the vector database.
    WARNING: This action cannot be undone!
    """
    rag_service = get_rag_service()
    success = rag_service.clear_knowledge_base()
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear knowledge base")
    
    return {"success": True, "message": "Knowledge base cleared successfully"}