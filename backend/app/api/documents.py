"""
Documents API Router
====================
Handles document upload, listing, deletion, and indexing.

Endpoints:
- POST /api/documents/upload: Upload a document
- GET /api/documents: List all documents
- DELETE /api/documents/{doc_id}: Delete a document
- POST /api/documents/{doc_id}/index: Index document into vector DB
"""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models import UploadResponse, IndexResponse, DocumentInfo
from app.services.document_service import get_document_service
from app.services.rag_service import get_rag_service

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, summary="Upload a document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document file to the knowledge base.
    
    Supported formats: PDF, TXT, MD (Markdown)
    
    After upload, you need to call the /index endpoint to vectorize it.
    """
    doc_service = get_document_service()
    
    # Validate file type
    allowed_extensions = doc_service.get_allowed_extensions()
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    # Save file
    doc_info = doc_service.save_uploaded_file(file_content, file.filename)
    
    return UploadResponse(
        success=True,
        message=f"File '{file.filename}' uploaded successfully",
        document=doc_info,
    )


@router.get("", summary="List all documents")
async def list_documents():
    """List all uploaded documents with metadata."""
    doc_service = get_document_service()
    documents = doc_service.list_documents()
    return {"documents": documents, "total": len(documents)}


@router.delete("/{doc_id}", summary="Delete a document")
async def delete_document(doc_id: str):
    """
    Delete a document and its vector data.
    
    - Removes the file from disk
    - Removes associated vectors from Chroma
    """
    doc_service = get_document_service()
    rag_service = get_rag_service()
    
    # Delete from vector DB first
    try:
        rag_service.delete_by_doc_id(doc_id)
    except Exception:
        pass  # May not exist in vector DB yet
    
    # Delete file
    success = doc_service.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"success": True, "message": f"Document {doc_id} deleted"}


@router.post("/{doc_id}/index", response_model=IndexResponse, summary="Index document")
async def index_document(doc_id: str):
    """
    Process and index a document into the vector database.
    
    Flow:
    1. Load the document file
    2. Split into chunks
    3. Generate embeddings
    4. Store in Chroma vector DB
    """
    doc_service = get_document_service()
    rag_service = get_rag_service()
    
    # Find document
    doc_list = doc_service.list_documents()
    target_doc = next((d for d in doc_list if d.doc_id == doc_id), None)
    
    if not target_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Load and split document
        split_docs = doc_service.load_document(doc_id, target_doc.filename)
        
        if not split_docs:
            return IndexResponse(
                success=False,
                message="Document is empty or could not be parsed",
            )
        
        # Index into vector DB
        rag_service.add_documents(split_docs)
        
        return IndexResponse(
            success=True,
            message=f"Successfully indexed {len(split_docs)} chunks",
            chunk_count=len(split_docs),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")