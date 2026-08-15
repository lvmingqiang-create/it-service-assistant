"""
Quality Check Agent Service
============================
Evaluates the quality of Agent responses and decides whether to accept or request a retry.

This Agent uses an LLM to assess response quality based on criteria like:
- Relevance to the original question
- Completeness of the answer
- Clarity and structure
- Actionable information

If the quality is below a threshold, it returns feedback for the Agent to improve.
"""

import json
from typing import Optional
from langchain_openai import ChatOpenAI
from app.config import settings
from app.utils.json_utils import extract_json


class QualityCheckAgentService:
    """
    Quality Check Agent that evaluates response quality.
    
    Returns:
        - passed: bool - Whether the response meets quality standards
        - score: float - Quality score (0.0 to 1.0)
        - feedback: str - Improvement suggestions if failed
    """

    def __init__(self):
        self.llm = self._create_llm()
        self.threshold = 0.7  # Minimum acceptable quality score

    def _create_llm(self):
        """Create LLM instance with low temperature for consistent evaluation."""
        return ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=0.0,
        )

    def evaluate(self, question: str, answer: str) -> dict:
        """
        Evaluate the quality of an Agent's response.
        
        Args:
            question: The original user question
            answer: The Agent's response to evaluate
            
        Returns:
            dict with keys:
                - passed: bool - Whether quality meets threshold
                - score: float - Quality score (0.0 to 1.0)
                - feedback: str - Improvement suggestions
        """
        system_prompt = f"""You are a quality assurance expert for an IT service AI assistant. 
Your job is to evaluate the quality of the assistant's responses.

Evaluation Criteria:
1. **Relevance**: Does the answer directly address the user's question?
2. **Completeness**: Does the answer provide sufficient detail and actionable information?
3. **Clarity**: Is the answer well-structured and easy to understand?
4. **Accuracy**: Does the answer appear factually correct and consistent?

Scoring:
- 0.9-1.0: Excellent - fully addresses the question with clear, actionable information
- 0.7-0.8: Good - addresses the question adequately, minor improvements possible
- 0.5-0.6: Fair - partially addresses the question, needs improvement
- 0.3-0.4: Poor - barely addresses the question, significant gaps
- 0.0-0.2: Unacceptable - does not address the question or is misleading

Pass/Fail Rule:
- If score >= {self.threshold}, set "passed" to true
- If score < {self.threshold}, set "passed" to false and provide specific feedback

Respond with ONLY a valid JSON object. No markdown, no code blocks, no explanation.

Example output:
{{"passed": true, "score": 0.85, "feedback": ""}}
{{"passed": false, "score": 0.45, "feedback": "The answer lacks specific actionable steps"}}

Required JSON schema:
{{"passed": true or false, "score": number between 0.0 and 1.0, "feedback": "string with improvement suggestions, or empty if passed"}}
"""

        user_prompt = f"""Question: {question}

Answer to evaluate: {answer}

Evaluate this response based on relevance, completeness, clarity, and accuracy."""

        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Extract JSON (handles markdown code blocks)
            content = self._extract_json(content)
            
            result = json.loads(content)
            
            # Validate and sanitize
            if not isinstance(result.get("score"), (int, float)):
                result["score"] = 0.5
            if not isinstance(result.get("passed"), bool):
                result["passed"] = result["score"] >= self.threshold
            
            # Apply threshold
            result["passed"] = result["score"] >= self.threshold
            
            if not result.get("feedback"):
                result["feedback"] = "" if result["passed"] else "Response quality below threshold"
            
            return result
            
        except Exception as e:
            # Fallback: if evaluation fails, assume passed to avoid infinite loops
            return {
                "passed": True,
                "score": 0.5,
                "feedback": f"Quality check error: {str(e)}",
            }

    def _extract_json(self, text: str) -> str:
        """Delegate to shared utility."""
        return extract_json(text)