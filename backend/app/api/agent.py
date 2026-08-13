"""
Agent API Router
================
Handles IT Service Agent endpoints with tool-use capability.

Endpoints:
- POST /api/agent/run: Run agent query with full thinking process
- GET /api/agent/tools: List available tools
"""

from fastapi import APIRouter
from app.models import AgentRequest, AgentResponse
from app.services.agent_service import get_agent_service

router = APIRouter()


@router.post("/run", response_model=AgentResponse, summary="Run agent query")
async def agent_run(request: AgentRequest):
    """
    Send a query to the IT Service Agent. The Agent will:
    1. Analyze the question
    2. Decide which tool(s) to use
    3. Execute tool calls
    4. Generate final answer
    
    Set show_thinking=true to see the full thought process.
    Pass history to maintain conversation context.
    """
    agent_service = get_agent_service()
    
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


@router.get("/tools", summary="List available agent tools")
async def list_tools():
    """Return the list of tools available to the agent."""
    agent_service = get_agent_service()
    return {"tools": agent_service.get_available_tools()}


@router.get("/tickets", summary="List all mock tickets")
async def list_tickets():
    """Return all mock IT tickets (for admin display)."""
    agent_service = get_agent_service()
    return {"tickets": agent_service.get_all_tickets()}