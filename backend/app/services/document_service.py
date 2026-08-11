"""
Document Processing Service Module
===================================
Responsible for document upload, reading, splitting, vectorization, and storage management.

Design:
- Supports multiple document formats (PDF/TXT/MD)
- Uses LangChain's document loaders and text splitters
- Splits documents into appropriately sized chunks for vectorization and retrieval
- Learning focus: Understand the complete document processing workflow in RAG (Load → Split → Vectorize → Store)

Why split documents?
- LLM context windows are limited, cannot input entire documents at once
- During retrieval, only need to return most relevant fragments, not entire documents
- Appropriate chunk size and overlap balance retrieval accuracy and context completeness
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.models import DocumentInfo


class DocumentService:
    """
    Document Processing Service Class
    
    Responsible for full document lifecycle management:
    1. Upload and save
    2. Content reading
    3. Text splitting
    4. Vectorization and storage (completed via RAG service)
    """

    def __init__(self):
        """
        Initialize document service
        Ensures upload directory exists
        """
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

        # Initialize text splitter
        # RecursiveCharacterTextSplitter is LangChain's recommended splitter
        # It recursively splits by characters, trying to preserve semantic unit integrity
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,        # Chunk size (characters)
            chunk_overlap=settings.chunk_overlap,  # Overlap size (maintains context continuity)
            length_function=len,                    # Length calculation function
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],  # Split separators
        )

    def save_uploaded_file(self, file_content: bytes, filename: str) -> DocumentInfo:
        """
        Save uploaded file to local storage
        
        Args:
            file_content: File content (bytes)
            filename: Original filename
        
        Returns:
            Document info object
        """
        # Generate unique document ID and storage filename
        doc_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]  # Get file extension
        stored_filename = f"{doc_id}{file_extension}"   # Use UUID as storage filename to avoid duplicates
        file_path = os.path.join(self.upload_dir, stored_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Return document info
        return DocumentInfo(
            doc_id=doc_id,
            filename=filename,
            size=len(file_content),
            upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            indexed=False,
        )

    def load_document(self, doc_id: str, original_filename: Optional[str] = None) -> List[str]:
        """
        Load and split document
        
        Workflow:
        1. Find file by document ID
        2. Select appropriate loader based on file type
        3. Read document content
        4. Split into text fragments
        
        Args:
            doc_id: Document ID
            original_filename: Original filename (used to determine file type)
        
        Returns:
            List of split text fragments
        """
        # Find file (need to traverse directory to find file corresponding to doc_id)
        file_path = self._find_file_by_doc_id(doc_id)
        if not file_path:
            raise FileNotFoundError(f"Document not found: {doc_id}")

        # Select loader based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".pdf":
            # PDF document loader
            loader = PyPDFLoader(file_path)
        elif file_ext in [".md", ".markdown"]:
            # Markdown document loader (use TextLoader to avoid network requests)
            loader = TextLoader(file_path)
        elif file_ext in [".txt"]:
            # Plain text loader
            loader = TextLoader(file_path)
        else:
            # Unsupported format, default to text
            print(f"[Warning] Unsupported file format: {file_ext}, treating as plain text")
            loader = TextLoader(file_path)

        # Load document
        documents = loader.load()

        # Split document
        split_docs = self.text_splitter.split_documents(documents)

        # Extract text content and add source metadata
        result = []
        for i, doc in enumerate(split_docs):
            # Record source information in metadata for displaying citations later
            doc.metadata["source"] = original_filename or os.path.basename(file_path)
            doc.metadata["doc_id"] = doc_id
            doc.metadata["chunk_index"] = i
            result.append(doc)

        return result

    def list_documents(self) -> List[DocumentInfo]:
        """
        Get list of all uploaded documents
        
        Returns:
            List of document info objects
        """
        documents = []

        if not os.path.exists(self.upload_dir):
            return documents

        # Traverse upload directory, read info for each file
        for filename in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, filename)
            if not os.path.isfile(file_path):
                continue

            # Extract doc_id from filename (storage format is {doc_id}.{ext})
            doc_id = os.path.splitext(filename)[0]

            # Get file info
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            upload_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            # Note: Simplified here, filename is doc_id, in production should have metadata storage
            documents.append(DocumentInfo(
                doc_id=doc_id,
                filename=filename,
                size=file_size,
                upload_time=upload_time,
                indexed=False,  # Simplified, should query from vector DB in production
            ))

        # Sort by upload time in descending order (newest first)
        documents.sort(key=lambda x: x.upload_time, reverse=True)
        return documents

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document
        
        Args:
            doc_id: Document ID
        
        Returns:
            Whether deletion was successful
        """
        file_path = self._find_file_by_doc_id(doc_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def _find_file_by_doc_id(self, doc_id: str) -> Optional[str]:
        """
        Find file path by document ID
        
        Because storage uses filename format {doc_id}.{ext}, need to traverse directory to find matching file.
        In production, should use database to store document metadata, simplified here.
        
        Args:
            doc_id: Document ID
        
        Returns:
            File path, returns None if not found
        """
        if not os.path.exists(self.upload_dir):
            return None

        for filename in os.listdir(self.upload_dir):
            if filename.startswith(doc_id):
                return os.path.join(self.upload_dir, filename)

        return None

    def get_file_path(self, doc_id: str) -> Optional[str]:
        """Get file path for document"""
        return self._find_file_by_doc_id(doc_id)

    def get_allowed_extensions(self) -> List[str]:
        """Get list of allowed file extensions"""
        return settings.allowed_file_types


# Global singleton instance
_doc_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """
    Get document service singleton
    """
    global _doc_service
    if _doc_service is None:
        _doc_service = DocumentService()
    return _doc_service