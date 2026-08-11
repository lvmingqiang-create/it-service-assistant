"""
RAG API Router
==============
Handles Retrieval-Augmented Generation endpoints.

Endpoints:
- POST /api/rag/query: Ask a question based on the knowledge base
- POST /api/rag/search: Pure semantic search without LLM generation
"""

from fastapi import APIRouter
from app.models import RAGRequest, RAGResponse, SourceDocument
from app.services.rag_service import get_rag_service
from app.services.llm_service import get_llm_service

router = APIRouter()


@router.post("/query", response_model=RAGResponse, summary="RAG Q&A")
async def rag_query(request: RAGRequest):
    """
    Ask a question and get an answer based on the knowledge base.
    
    Flow:
    1. Retrieve relevant document chunks from vector DB
    2. Build a prompt with the retrieved context + user question
    3. Send to LLM to generate answer
    4. Return answer + source citations
    """
    rag_service = get_rag_service()
    llm_service = get_llm_service()
    
    # Step 1: Retrieve relevant documents
    source_docs = rag_service.search(request.question)
    
    # Step 2: Build context from retrieved documents
    context_parts = []
    for i, doc in enumerate(source_docs, 1):
        context_parts.append(f"[Document {i}] Source: {doc.source}\nContent: {doc.content}")
    
    context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
    
    # Step 3: Build prompt and call LLM
    system_prompt = """You are an IT service assistant. Answer the user's question based ONLY on the provided context.

## Answering Rules
1. Only answer based on the provided reference documents, do not fabricate information
2. If there is no relevant content in the reference documents, clearly state "Unable to answer this question based on current knowledge base"
3. Answers should be accurate, concise, and well-organized
4. For step-by-step questions, use numbered lists
5. You may organize and summarize, but do not change the original meaning
6. Always cite the source documents you used in your answer.
7. [Mandatory] All answers MUST end with "Thank you." as the final sentence, do not add anything after it
"""

    user_prompt = f"""Context:
{context}

Question: {request.question}

Answer:"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    answer = llm_service.chat(messages)
    
    # Step 4: Return response with sources
    return RAGResponse(
        answer=answer,
        sources=source_docs,
    )


@router.post("/search", summary="Semantic search only")
async def rag_search(request: RAGRequest):
    """
    Perform pure semantic search without LLM generation.
    Returns the most relevant document chunks directly.
    """
    rag_service = get_rag_service()
    source_docs = rag_service.search(request.question)
    
    return {
        "results": source_docs,
        "total": len(source_docs),
    }