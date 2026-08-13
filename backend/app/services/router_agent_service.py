"""
Router Agent Service
=====================
Routes user questions to the appropriate Agent based on question type.

Design:
- Uses LLM to classify the question into categories
- Returns routing decision with confidence score
- Supports: IT Service (knowledge base, tickets, FAQ) vs IT Operations (system status, service management)
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
import json


class RouterAgentService:
    """
    Router Agent Service
    
    Analyzes user questions and determines which Agent should handle them.
    """

    def __init__(self):
        self.llm = self._create_llm()

    def _create_llm(self) -> ChatOpenAI:
        """Create LLM instance for routing classification."""
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=0.1,  # Low temperature for consistent classification
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM response.
        
        LLMs often wrap JSON in markdown code blocks or add extra text.
        This method extracts the JSON object reliably.
        """
        # Remove markdown code blocks if present
        if "```" in text:
            # Try to find JSON between ``` markers
            import re
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
            # Fallback: find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return text[start:end+1]
        
        # If no code blocks, try to find JSON object directly
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        
        # Return original text as fallback
        return text

    def route_question(self, question: str) -> dict:
        """
        Route a question to the appropriate Agent.
        
        Args:
            question: User's question
            
        Returns:
            dict with keys:
                - target: "service" | "operations" | "unknown"
                - confidence: float (0-1)
                - reason: str (explanation of routing decision)
        """
        system_prompt = """You are a question router for an IT service system. Your job is to classify user questions into one of two categories.

## Categories

**"service"** - End-user IT support questions:
- How to use email, software, hardware
- Password reset, account issues
- General troubleshooting ("my computer is slow", "printer not working")
- Knowledge base, FAQ, ticket status
- Examples: "I lost my phone, what should I do?", "How to reset my email password?"

**"operations"** - System administration and infrastructure management:
- Server status, health checks
- Service management (start/stop/restart nginx, mysql, redis)
- Log queries ("show nginx logs", "check error logs")
- Resource monitoring ("check CPU usage", "monitor CPU", "disk space")
- Examples: "restart nginx service", "what is the CPU usage?", "show me the logs"

## Decision Rules
- Keywords: "check", "monitor", "status", "logs", "CPU", "memory", "disk", "restart", "service" → "operations"
- Keywords: "how to", "what should I do", "help", "guide", "password", "email" → "service"
- End user seeking help → "service"
- Managing/monitoring infrastructure → "operations"
- Ambiguous → "service"

## Output Format

You MUST respond with ONLY a valid JSON object. No markdown, no code blocks, no explanation, no additional text.

Example output:
{"target": "operations", "confidence": 0.95, "reason": "Question asks to monitor CPU usage, which is a system resource monitoring task"}

Required JSON schema:
{"target": "service" or "operations" or "unknown", "confidence": number between 0.0 and 1.0, "reason": "string explanation"}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Question: {question}"),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Extract JSON from LLM response (handles markdown code blocks, etc.)
            content = self._extract_json(content)
            
            # Parse JSON response
            result = json.loads(content)
            
            # Validate response
            if result.get("target") not in ["service", "operations", "unknown"]:
                result["target"] = "service"  # Default fallback
            if not isinstance(result.get("confidence"), (int, float)):
                result["confidence"] = 0.5
            if not result.get("reason"):
                result["reason"] = "Default routing"
            
            return result
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback: default to service agent
            return {
                "target": "service",
                "confidence": 0.5,
                "reason": f"Routing error, defaulting to service: {str(e)}",
            }