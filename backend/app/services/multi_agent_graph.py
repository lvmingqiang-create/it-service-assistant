"""
Multi-Agent Graph Service using LangGraph
==========================================
Orchestrates multiple Agents (Router, Service, Operations) into a cohesive workflow.

Architecture:
    User Input
        ↓
    [Router Agent] → Classifies question type
        ↓
    ┌─────────┴─────────┐
    ↓                   ↓
[Service Agent]   [Operations Agent]
    ↓                   ↓
    └─────────┬─────────┘
              ↓
        [Final Response]

Design:
- Uses LangGraph StateGraph for workflow orchestration
- Shared State carries question, routing decision, and final answer
- Conditional edges route to the appropriate Agent based on classification
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.services.router_agent_service import RouterAgentService
from app.services.agent_service import AgentService
from app.services.operations_agent_service import OperationsAgentService


class AgentState(TypedDict):
    """
    Shared state passed between all nodes in the graph.
    
    Attributes:
        question: The original user question
        history: Conversation history (list of {role, content} dicts)
        show_thinking: Whether to include detailed thinking process
        target: Routing decision ("service", "operations", or "unknown")
        confidence: Confidence score of routing decision (0-1)
        reason: Explanation of routing decision
        answer: Final answer from the selected Agent
        thinking_process: Detailed thinking process (if show_thinking=True)
        error: Error message if any step fails
    """
    question: str
    history: list
    show_thinking: bool
    target: Optional[str]
    confidence: Optional[float]
    reason: Optional[str]
    answer: Optional[str]
    thinking_process: Optional[list]
    error: Optional[str]


class MultiAgentGraph:
    """
    Multi-Agent Graph orchestrator.
    
    Creates and manages the LangGraph workflow that routes questions
    to the appropriate Agent and collects the response.
    """

    def __init__(self):
        self.router = RouterAgentService()
        self.service_agent = AgentService()
        self.operations_agent = OperationsAgentService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Graph structure:
            START → router_node → [conditional edge] → service_node OR operations_node → END
        """
        # Create state graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("service", self._service_node)
        workflow.add_node("operations", self._operations_node)

        # Set entry point
        workflow.set_entry_point("router")

        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "service": "service",
                "operations": "operations",
                "unknown": "service",  # Default to service for unknown
            },
        )

        # Add edges from agents to END
        workflow.add_edge("service", END)
        workflow.add_edge("operations", END)

        # Compile graph
        return workflow.compile()

    def _router_node(self, state: AgentState) -> dict:
        """
        Router node: Classifies the question and decides which Agent to use.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with routing decision
        """
        routing_result = self.router.route_question(state["question"])
        
        return {
            "target": routing_result["target"],
            "confidence": routing_result["confidence"],
            "reason": routing_result["reason"],
        }

    def _service_node(self, state: AgentState) -> dict:
        """
        Service Agent node: Handles IT service questions.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with answer from Service Agent
        """
        try:
            answer, steps, tools_used = self.service_agent.run_query(
                query=state["question"],
                history=state["history"],
                show_thinking=state["show_thinking"],
            )
            
            return {
                "answer": answer,
                "thinking_process": steps if state["show_thinking"] else [],
            }
        except Exception as e:
            return {
                "answer": f"Sorry, the Service Agent encountered an error: {str(e)}",
                "error": str(e),
            }

    def _operations_node(self, state: AgentState) -> dict:
        """
        Operations Agent node: Handles IT operations questions.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with answer from Operations Agent
        """
        try:
            answer, steps, tools_used = self.operations_agent.run_query(
                query=state["question"],
                history=state["history"],
                show_thinking=state["show_thinking"],
            )
            
            return {
                "answer": answer,
                "thinking_process": steps if state["show_thinking"] else [],
            }
        except Exception as e:
            return {
                "answer": f"Sorry, the Operations Agent encountered an error: {str(e)}",
                "error": str(e),
            }

    def _route_decision(self, state: AgentState) -> str:
        """
        Conditional edge function: Determines which node to go to next.
        
        Args:
            state: Current graph state
            
        Returns:
            Node name: "service", "operations", or "unknown"
        """
        target = state.get("target", "unknown")
        print(f"[MultiAgentGraph] Routing decision: target={target}, confidence={state.get('confidence')}, reason={state.get('reason')}")
        return target

    def run(self, question: str, history: list = None, show_thinking: bool = False) -> dict:
        """
        Run the multi-agent workflow.
        
        Args:
            question: User's question
            history: Conversation history (optional)
            show_thinking: Whether to include detailed thinking process
            
        Returns:
            dict with keys:
                - answer: Final answer
                - target: Which Agent handled the question
                - confidence: Routing confidence
                - reason: Routing explanation
                - thinking_process: Detailed thinking process (if show_thinking=True)
        """
        initial_state: AgentState = {
            "question": question,
            "history": history or [],
            "show_thinking": show_thinking,
            "target": None,
            "confidence": None,
            "reason": None,
            "answer": None,
            "thinking_process": None,
            "error": None,
        }

        # Execute graph
        final_state = self.graph.invoke(initial_state)

        return {
            "answer": final_state.get("answer", "No answer generated."),
            "target": final_state.get("target", "unknown"),
            "confidence": final_state.get("confidence", 0),
            "reason": final_state.get("reason", ""),
            "thinking_process": final_state.get("thinking_process", []),
            "error": final_state.get("error"),
        }