"""
Multi-Agent Graph Service using LangGraph
==========================================
Orchestrates multiple Agents (Router, Service, Operations) into a cohesive workflow
with a Quality Check loop for self-correction.

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
    [Quality Check Agent]
              ↓
      Quality >= threshold?
        ↓           ↓
      YES          NO (retry, max 2)
        ↓           ↓
      END    ← back to Agent with feedback

Design:
- Uses LangGraph StateGraph for workflow orchestration
- Shared State carries question, routing decision, answer, and quality info
- Conditional edges route to the appropriate Agent based on classification
- Quality Check loop enables self-correction with retry limit
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.services.router_agent_service import RouterAgentService
from app.services.agent_service import AgentService
from app.services.operations_agent_service import OperationsAgentService
from app.services.quality_check_agent_service import QualityCheckAgentService


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
        answer: Current answer from the selected Agent
        thinking_process: Detailed thinking process (if show_thinking=True)
        error: Error message if any step fails
        quality_retry_count: Number of quality check retries (max 2)
        quality_passed: Whether the last quality check passed
        quality_score: Quality check score (0-1)
        quality_feedback: Feedback from quality check for retry
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
    quality_retry_count: int
    quality_passed: Optional[bool]
    quality_score: Optional[float]
    quality_feedback: Optional[str]


class MultiAgentGraph:
    """
    Multi-Agent Graph orchestrator.
    
    Creates and manages the LangGraph workflow that routes questions
    to the appropriate Agent, then checks quality and optionally retries.
    """

    MAX_RETRIES = 2  # Maximum number of quality check retries

    def __init__(self):
        self.router = RouterAgentService()
        self.service_agent = AgentService()
        self.operations_agent = OperationsAgentService()
        self.quality_check = QualityCheckAgentService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Graph structure:
            START → router_node → [conditional edge] → service_node OR operations_node
                                                              ↓
                                                    quality_check_node
                                                              ↓
                                            [conditional edge] → END or retry
        """
        # Create state graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("service", self._service_node)
        workflow.add_node("operations", self._operations_node)
        workflow.add_node("quality_check", self._quality_check_node)

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

        # Add edges from agents to quality check
        workflow.add_edge("service", "quality_check")
        workflow.add_edge("operations", "quality_check")

        # Add conditional edges from quality check
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_decision,
            {
                "retry_service": "service",
                "retry_operations": "operations",
                "end": END,
            },
        )

        # Compile graph
        return workflow.compile()

    def _router_node(self, state: AgentState) -> dict:
        """
        Router node: Classifies the question and decides which Agent to use.
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
        If retrying, includes quality feedback in the prompt context.
        """
        print(f"[MultiAgentGraph] >>> Executing SERVICE node for question: {state['question'][:50]}...")
        try:
            # If this is a retry, append feedback to the question
            query = state["question"]
            if state.get("quality_retry_count", 0) > 0 and state.get("quality_feedback"):
                query = (
                    f"{state['question']}\n\n"
                    f"Previous answer quality feedback: {state['quality_feedback']}\n"
                    f"Please improve your answer based on this feedback."
                )
            
            answer, steps, tools_used = self.service_agent.run_query(
                query=query,
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
        If retrying, includes quality feedback in the prompt context.
        """
        print(f"[MultiAgentGraph] >>> Executing OPERATIONS node for question: {state['question'][:50]}...")
        try:
            # If this is a retry, append feedback to the question
            query = state["question"]
            if state.get("quality_retry_count", 0) > 0 and state.get("quality_feedback"):
                query = (
                    f"{state['question']}\n\n"
                    f"Previous answer quality feedback: {state['quality_feedback']}\n"
                    f"Please improve your answer based on this feedback."
                )
            
            answer, steps, tools_used = self.operations_agent.run_query(
                query=query,
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

    def _quality_check_node(self, state: AgentState) -> dict:
        """
        Quality Check node: Evaluates the Agent's response quality.
        """
        if not state.get("answer"):
            return {
                "quality_passed": True,  # Skip if no answer (error case)
                "quality_score": 0.0,
                "quality_feedback": "No answer to evaluate",
            }
        
        result = self.quality_check.evaluate(
            question=state["question"],
            answer=state["answer"],
        )
        
        quality_retry_count = state.get("quality_retry_count", 0)
        
        # If quality failed but we've hit max retries, force pass
        if not result["passed"] and quality_retry_count >= self.MAX_RETRIES:
            result["passed"] = True
            result["feedback"] = (
                f"Quality below threshold (score: {result['score']:.2f}), "
                f"but max retries ({self.MAX_RETRIES}) reached. Returning best effort answer."
            )
        
        return {
            "quality_passed": result["passed"],
            "quality_score": result["score"],
            "quality_feedback": result["feedback"],
            "quality_retry_count": quality_retry_count + 1 if not result["passed"] else quality_retry_count,
        }

    def _route_decision(self, state: AgentState) -> str:
        """
        Conditional edge function: Determines which Agent node to go to next.
        """
        target = state.get("target", "unknown")
        print(f"[MultiAgentGraph] Routing decision: target={target}, confidence={state.get('confidence')}, reason={state.get('reason')}")
        return target

    def _quality_decision(self, state: AgentState) -> str:
        """
        Conditional edge function: Determines whether to retry or end.
        
        Returns:
            "retry_service" - Retry Service Agent with feedback
            "retry_operations" - Retry Operations Agent with feedback
            "end" - Quality passed or max retries reached
        """
        quality_passed = state.get("quality_passed", True)
        target = state.get("target", "unknown")
        quality_retry_count = state.get("quality_retry_count", 0)
        
        if quality_passed:
            print(f"[MultiAgentGraph] Quality check PASSED (score: {state.get('quality_score'):.2f})")
            return "end"
        else:
            print(f"[MultiAgentGraph] Quality check FAILED (score: {state.get('quality_score'):.2f}), retry {quality_retry_count}/{self.MAX_RETRIES}")
            # Route back to the same Agent that handled the question
            if target == "operations":
                return "retry_operations"
            else:
                return "retry_service"

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
                - quality_score: Quality check score
                - quality_passed: Whether quality check passed
                - quality_feedback: Quality check feedback
                - quality_retry_count: Number of retries performed
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
            "quality_retry_count": 0,
            "quality_passed": None,
            "quality_score": None,
            "quality_feedback": None,
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
            "quality_score": final_state.get("quality_score", 0),
            "quality_passed": final_state.get("quality_passed", True),
            "quality_feedback": final_state.get("quality_feedback", ""),
            "quality_retry_count": final_state.get("quality_retry_count", 0),
        }