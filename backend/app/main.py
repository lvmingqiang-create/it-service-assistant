"""
FastAPI Application Entry Point
=================================
Responsible for creating FastAPI application instance, registering routes, configuring middleware.

Design:
- Entry file kept concise, mainly responsible for assembly and configuration
- All business logic placed in services and api modules
- Automatically creates necessary directories on startup to ensure smooth application startup
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings

# ========== Create FastAPI Application ==========
# title and description will be displayed in auto-generated API documentation page (/docs)
app = FastAPI(
    title=settings.app_name,
    description="Enterprise IT Service Smart Assistant - Self-developed Project Skeleton\n\nSupports chat Q&A, RAG knowledge base Q&A, IT service Agent, and more",
    version="1.0.0",
)

# ========== Configure CORS Cross-Origin ==========
# When developing with frontend-backend separation, need to configure cross-origin
# For teaching convenience, allows all origins by default
# In production, should configure specific frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,       # Allowed origins
    allow_credentials=True,                    # Allow credentials
    allow_methods=["*"],                       # Allow all HTTP methods
    allow_headers=["*"],                       # Allow all request headers
)


# ========== Ensure Necessary Directories Exist ==========
def ensure_directories():
    """
    Ensure directories required by application exist
    Automatically created on first startup, avoid errors due to missing directories
    """
    dirs_to_create = [
        settings.upload_dir,                    # Upload file directory
        settings.chroma_persist_directory,      # Vector database directory
        "./data",                               # Data root directory
    ]
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"[Startup] Created directory: {directory}")


# ========== Register API Routes ==========
# Various functional module routes are defined in app/api/ directory, imported and registered here
from app.api.chat import router as chat_router        # Chat API
from app.api.rag import router as rag_router          # RAG API
from app.api.agent import router as agent_router      # Agent API
from app.api.operations_agent import router as operations_agent_router  # Operations Agent API
from app.api.multi_agent import router as multi_agent_router  # Multi-Agent API
from app.api.documents import router as documents_router  # Document Management API
from app.api.admin import router as admin_router      # Admin API

# Register routes, each module has its own prefix and tag (easy to distinguish in API docs)
app.include_router(chat_router, prefix="/api/chat", tags=["Chat Q&A"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG Knowledge Base"])
app.include_router(agent_router, prefix="/api/agent", tags=["IT Service Agent"])
app.include_router(operations_agent_router, prefix="/api/operations-agent", tags=["IT Operations Agent"])
app.include_router(multi_agent_router, prefix="/api/multi-agent", tags=["Multi-Agent"])
app.include_router(documents_router, prefix="/api/documents", tags=["Document Management"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin API"])


# ========== Root Path ==========
@app.get("/", summary="Root Path - Health Check")
async def root():
    """
    Health check endpoint, used to confirm service is running normally
    """
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs (Interactive API Documentation)",
    }


# ========== Startup Event ==========
@app.on_event("startup")
async def startup_event():
    """
    Initialization operations executed when application starts
    """
    print(f"{'='*50}")
    print(f"🚀 {settings.app_name} Starting...")
    print(f"📋 Environment: {settings.environment}")
    print(f"🔧 LLM Provider: {settings.llm_provider}")
    print(f"📚 Vector DB Path: {settings.chroma_persist_directory}")
    print(f"{'='*50}")
    
    # Ensure directories exist
    ensure_directories()
    
    print("✅ Application started successfully!")


# ========== Mount Static Files ==========
# Mount frontend static files, so FastAPI can directly serve frontend pages
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
    print(f"[Startup] Mounted frontend directory: {frontend_dir}")