"""
IT Operations Agent API Endpoints

Provides REST API for IT Operations Agent queries.
"""

from fastapi import APIRouter, HTTPException
from app.models import AgentRequest, AgentResponse
from app.services.operations_agent_service import OperationsAgentService

router = APIRouter(tags=["Operations Agent"])

_operations_agent = None


def get_operations_agent() -> OperationsAgentService:
    """Get or create Operations Agent singleton instance."""
    global _operations_agent
    if _operations_agent is None:
        _operations_agent = OperationsAgentService()
    return _operations_agent


@router.post("/run", response_model=AgentResponse, summary="Run operations agent query")
async def operations_agent_run(request: AgentRequest):
    """
    Send a query to the IT Operations Agent. The Agent will:
    1. Analyze the operations request
    2. Decide which tool(s) to use (system status, service management, logs, resources)
    3. Execute tool calls
    4. Generate final answer
    
    Set show_thinking=true to see the full thought process.
    Pass history to maintain conversation context.
    """
    agent_service = get_operations_agent()
    
    answer, steps, tools_used = agent_service.run_query(
        query=request.query,
        show_thinking=request.show_thinking,
        history=request.history,
    )
    
    return AgentResponse(
        answer=answer,
        steps=steps,
        tools_used=tools_used,
    )