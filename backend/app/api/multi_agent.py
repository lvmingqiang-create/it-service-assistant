"""
Multi-Agent API Endpoint
=========================
Provides API endpoint for the multi-agent workflow.

Endpoint:
    POST /api/multi-agent/run
    
Request Body:
    {
        "question": "User's question",
        "history": [{"role": "user", "content": "..."}, ...],
        "show_thinking": true/false
    }
    
Response:
    {
        "answer": "Final answer from the selected Agent",
        "target": "service" or "operations",
        "confidence": 0.95,
        "reason": "Explanation of routing decision",
        "thinking_process": [...],
        "error": null
    }
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.multi_agent_graph import MultiAgentGraph

router = APIRouter(tags=["Multi-Agent"])


class MultiAgentRequest(BaseModel):
    """Request model for multi-agent workflow."""
    question: str
    history: list = []
    show_thinking: bool = False


# Singleton pattern for graph instance
_multi_agent_graph = None


def get_multi_agent_graph() -> MultiAgentGraph:
    """Get or create the multi-agent graph singleton."""
    global _multi_agent_graph
    if _multi_agent_graph is None:
        _multi_agent_graph = MultiAgentGraph()
    return _multi_agent_graph


@router.post("/run")
async def multi_agent_run(request: MultiAgentRequest):
    """
    Run the multi-agent workflow.
    
    The workflow:
    1. Router Agent classifies the question
    2. Routes to Service Agent or Operations Agent
    3. Selected Agent processes the question
    4. Returns the answer with routing metadata
    """
    graph = get_multi_agent_graph()
    
    result = graph.run(
        question=request.question,
        history=request.history,
        show_thinking=request.show_thinking,
    )
    
    return result