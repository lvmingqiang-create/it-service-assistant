"""
Data Models Module
==================
Defines all API request/response data structures and internal data models.

Design Notes:
- Uses Pydantic for data validation and automatic API documentation
- Request and response models are separated for clear responsibilities
- All fields have descriptions for better API doc readability
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== Chat Models ====================

class ChatMessage(BaseModel):
    """Single chat message in a conversation."""
    role: str = Field(description="Message role: user/assistant/system")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    messages: List[ChatMessage] = Field(description="Conversation history")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    reply: str = Field(description="AI reply content")
    role: str = "assistant"


# ==================== RAG Models ====================

class RAGRequest(BaseModel):
    """Request body for RAG Q&A endpoint."""
    question: str = Field(description="User question")
    history: Optional[List[ChatMessage]] = Field(None, description="Chat history")


class SourceDocument(BaseModel):
    """A source document chunk referenced in RAG answers."""
    content: str = Field(description="Document chunk content")
    source: str = Field(description="Source document name")
    score: Optional[float] = Field(None, description="Similarity score")


class RAGResponse(BaseModel):
    """Response body for RAG Q&A endpoint."""
    answer: str = Field(description="Answer based on knowledge base")
    sources: List[SourceDocument] = Field(description="List of source documents")


# ==================== Agent Models ====================

class AgentStep(BaseModel):
    """A single step in the Agent's thinking process."""
    step_type: str = Field(description="Step type: thought/action/observation")
    content: str = Field(description="Step content")
    tool: Optional[str] = Field(None, description="Tool name (for action steps)")


class AgentRequest(BaseModel):
    """Request body for Agent endpoint."""
    query: str = Field(description="User question or task")
    show_thinking: bool = Field(True, description="Whether to show thinking process")


class AgentResponse(BaseModel):
    """Response body for Agent endpoint."""
    answer: str = Field(description="Final answer")
    steps: List[AgentStep] = Field(default_factory=list, description="Thinking steps")
    tools_used: List[str] = Field(default_factory=list, description="Tools used")


# ==================== Document Management Models ====================

class DocumentInfo(BaseModel):
    """Document metadata for listing display."""
    doc_id: str = Field(description="Document ID")
    filename: str = Field(description="Document filename")
    size: int = Field(description="File size in bytes")
    upload_time: str = Field(description="Upload time")
    indexed: bool = Field(False, description="Whether indexed in vector DB")
    chunk_count: Optional[int] = Field(None, description="Number of chunks")


class UploadResponse(BaseModel):
    """Response for file upload."""
    success: bool = Field(description="Whether upload succeeded")
    message: str = Field(description="Status message")
    document: Optional[DocumentInfo] = Field(None, description="Uploaded document info")


class IndexRequest(BaseModel):
    """Request to index a document into the vector database."""
    doc_id: str = Field(description="Document ID to index")


class IndexResponse(BaseModel):
    """Response for document indexing."""
    success: bool = Field(description="Whether indexing succeeded")
    message: str = Field(description="Status message")
    chunk_count: Optional[int] = Field(None, description="Number of chunks created")


# ==================== Ticket Models ====================

class TicketInfo(BaseModel):
    """IT ticket information (mock data for demo)."""
    ticket_id: str = Field(description="Ticket ID")
    title: str = Field(description="Ticket title")
    status: str = Field(description="Ticket status")
    submitter: str = Field(description="Person who submitted the ticket")
    create_time: str = Field(description="Creation time")
    assignee: Optional[str] = Field(None, description="Assigned engineer")
    description: str = Field(description="Problem description")


# ==================== Admin / Stats Models ====================

class KBStats(BaseModel):
    """Knowledge base statistics."""
    total_documents: int = Field(0, description="Total number of documents")
    total_chunks: int = Field(0, description="Total number of vector chunks")
    collection_name: str = Field("", description="Chroma collection name")
    persist_directory: str = Field("", description="Chroma storage path")
