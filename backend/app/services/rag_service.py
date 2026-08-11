"""
RAG Service Module
==================
Implements Retrieval-Augmented Generation (RAG),
enabling LLM to answer questions based on knowledge base documents.

Design:
- Uses Chroma as vector database (lightweight, local file storage, no extra deployment needed)
- Retrieves most relevant document fragments as context for LLM
- Shows citation sources to make answers more credible
- Learning focus: Understand RAG core principles (Retrieve → Augment → Generate) and vector database role

RAG Workflow:
1. Document vectorization: Split documents into fragments, convert each fragment to vector and store in vector database
2. Retrieval: When user asks a question, convert it to vector and find most similar document fragments
3. Augmentation: Assemble retrieved fragments and question into a prompt
4. Generation: LLM generates answer based on provided context
"""

from typing import List, Optional
import re
import chromadb
from langchain_chroma import Chroma

from app.config import settings
from app.services.llm_service import get_llm_service
from app.models import SourceDocument


class RAGService:
    """
    RAG Service Class
    
    Responsible for knowledge base construction, retrieval, and Q&A functionality.
    """

    def __init__(self):
        """
        Initialize RAG service
        Creates or loads Chroma vector database
        """
        self.llm_service = get_llm_service()
        self.embeddings = self.llm_service.get_embedding_instance()
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = settings.chroma_collection_name

        # Create Chroma vector store
        # Chroma automatically persists vectors to local files
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def add_documents(self, documents: List) -> int:
        """
        Add documents to vector database
        
        Args:
            documents: List of LangChain Document objects (already split document fragments)
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        # Use LangChain's Chroma interface to add documents
        # Internally automatically calls embedding model to convert text to vectors
        self.vector_store.add_documents(documents)

        print(f"[RAG] Added {len(documents)} document fragments to vector store")
        return len(documents)

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> int:
        """
        Add text directly to vector database
        
        Args:
            texts: List of texts
            metadatas: Corresponding metadata list
        
        Returns:
            Number of texts added
        """
        if not texts:
            return 0

        self.vector_store.add_texts(texts=texts, metadatas=metadatas or [])
        return len(texts)

    def search(self, query: str, top_k: Optional[int] = None) -> List[SourceDocument]:
        """
        Retrieve most relevant document fragments from knowledge base
        
        Args:
            query: User question
            top_k: Number of results to return, defaults to configured value
        
        Returns:
            List of relevant document fragments (with source information)
        """
        if top_k is None:
            top_k = settings.rag_top_k

        # Use similarity search
        # Returns (Document, score) tuple list, lower score means more similar
        results = self.vector_store.similarity_search_with_score(query, k=top_k)

        # Convert to SourceDocument format
        source_docs = []
        for doc, score in results:
            source_docs.append(SourceDocument(
                content=doc.page_content,
                source=doc.metadata.get("source", "Unknown source"),
                score=float(score),
            ))

        return source_docs

    def answer_question(self, question: str, history: Optional[List[dict]] = None) -> tuple:
        """
        Answer question based on knowledge base
        
        Complete RAG workflow:
        1. Retrieve relevant documents
        2. Build prompt (with context and question)
        3. Call LLM to generate answer
        
        Args:
            question: User question
            history: Conversation history (optional)
        
        Returns:
            (answer_text, citation_sources)
        """
        # Step 1: Retrieve relevant documents
        source_docs = self.search(question)

        if not source_docs:
            return "No related content found in the knowledge base. Please try a different question or upload relevant documents first.", []

        # Step 2: Build context
        context_parts = []
        for i, doc in enumerate(source_docs, 1):
            context_parts.append(f"[Document {i}] Source: {doc.source}\nContent: {doc.content}")

        context = "\n\n".join(context_parts)

        # Step 3: Build system prompt
        system_prompt = f"""You are a professional enterprise IT service assistant. Please answer the user's question based on the provided reference documents.

## Answering Rules
1. Only answer based on the provided reference documents, do not fabricate information
2. If there is no relevant content in the reference documents, clearly state "Unable to answer this question based on current knowledge base"
3. Answers should be accurate, concise, and well-organized
4. For step-by-step questions, use numbered lists
5. You may organize and summarize, but do not change the original meaning
6. [Mandatory] All answers MUST end with "Thank you." as the final sentence, do not add anything after it

## Reference Documents
{context}

Please answer the user's question in English."""

        # Step 4: Call LLM to generate answer
        messages = []
        if history:
            # Only keep recent conversation turns to avoid context being too long
            messages = history[-6:] if len(history) > 6 else history

        messages.append({"role": "user", "content": question})

        answer = self.llm_service.chat(messages, system_prompt=system_prompt)

        # Debug: Log whether the LLM followed the "Thank you" instruction
        import sys
        if answer.strip().endswith("Thank you."):
            print("[RAG Debug] ✅ LLM followed instruction: answer ends with 'Thank you.'", flush=True)
        else:
            print(f"[RAG Debug] ❌ LLM did NOT follow instruction. Answer ending: '...{answer.strip()[-30:]}'", flush=True)
            sys.stdout.flush()

        return answer, source_docs

    def get_knowledge_base_status(self) -> dict:
        """
        Get knowledge base status information
        
        Returns:
            Knowledge base status dictionary
        """
        # Get vector count in collection
        try:
            collection = self.vector_store._collection
            total_chunks = collection.count()
        except Exception:
            total_chunks = 0

        # Count how many unique documents (deduplicate by source metadata)
        # Note: Chroma doesn't have a direct interface, need full query, simplified here
        total_documents = 0
        try:
            # Get all metadata and deduplicate source field
            results = collection.get(include=["metadatas"])
            sources = set()
            for meta in results["metadatas"]:
                if meta and "source" in meta:
                    sources.add(meta["source"])
            total_documents = len(sources)
        except Exception:
            pass

        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def delete_by_doc_id(self, doc_id: str) -> bool:
        """
        Delete all vectors corresponding to a document ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            Whether deletion was successful
        """
        try:
            # Chroma filters by metadata for deletion
            # Note: Deletion requires finding corresponding IDs first
            collection = self.vector_store._collection
            results = collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"]
            )
            if results["ids"]:
                collection.delete(ids=results["ids"])
                print(f"[RAG] Deleted {len(results['ids'])} vectors for document {doc_id}")
                return True
            return False
        except Exception as e:
            print(f"[RAG Delete Error] {e}")
            return False

    def clear_knowledge_base(self) -> bool:
        """
        Clear entire knowledge base (use with caution)
        
        Returns:
            Whether clearing was successful
        """
        try:
            collection = self.vector_store._collection
            # Delete all data in collection
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
            print(f"[RAG] Cleared knowledge base, deleted {len(all_ids)} vectors")
            return True
        except Exception as e:
            print(f"[RAG Clear Error] {e}")
            return False


# Global singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get RAG service singleton
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service