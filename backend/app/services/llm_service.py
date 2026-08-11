"""
LLM Service Module
==================
Encapsulates large language model calls, supporting multiple providers (multi-provider architecture).

Design:
- Uses factory pattern to create different LLM instances based on configuration
- Currently implements OpenAI compatible interface (can integrate with Volcengine/Doubao/Tongyi Qianwen, etc.)
- Unified call interface, business logic doesn't care about which LLM is used underneath
- Learning focus: Understand LangChain's ChatModel abstraction and multi-provider switching design pattern

Why use LangChain?
- LangChain provides a unified LLM abstraction layer, switching LLM providers only requires changing configuration
- Built-in conversation history management, message format conversion, etc.
- Future extensions like Agent, RAG can directly use LangChain components
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from typing import List, Optional

from app.config import settings


class LLMService:
    """
    LLM Service Class
    
    Encapsulates all interactions with large language models, providing a unified call interface.
    Supports multi-turn conversations, system prompts, etc.
    """

    def __init__(self):
        """
        Initialize LLM service
        Creates corresponding LLM instance based on configuration
        """
        self.llm = self._create_llm()
        self.embedding_model = self._create_embedding()

    def _create_llm(self) -> ChatOpenAI:
        """
        Create LLM instance (factory method)
        
        Creates corresponding LLM instance based on settings.llm_provider value.
        Currently supports:
        - openai_compatible: OpenAI compatible interface (Volcengine/Doubao/Tongyi Qianwen, etc.)
        
        Why use ChatOpenAI class to兼容 other platforms?
        Because many domestic platforms (Volcengine, Tongyi Qianwen, DeepSeek, etc.) provide
        API specifications fully compatible with OpenAI, so you can directly use ChatOpenAI class,
        only need to modify base_url and api_key to integrate different platforms.
        """
        provider = settings.llm_provider.lower()

        if provider == "openai_compatible":
            # OpenAI compatible mode (supports Volcengine/Doubao/Tongyi Qianwen/DeepSeek, etc.)
            # Only need to modify base_url and api_key to integrate different platforms
            return ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                temperature=0.7,        # Temperature: 0=most deterministic, 1=most random
                max_tokens=2048,        # Maximum generated tokens
            )
        else:
            # Default to compatible mode
            print(f"[Warning] Unknown LLM provider: {provider}, using default compatible mode")
            return ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                temperature=0.7,
                max_tokens=2048,
            )

    def _create_embedding(self):
        """
        Create embedding model instance
        
        Embedding model is used to convert text to vectors, which is the foundation of RAG functionality.
        Also uses OpenAI compatible interface for easy switching between different platforms' embedding models.
        """
        from langchain_openai import OpenAIEmbeddings
        
        # If no separate embedding model API Key is configured, use LLM's
        api_key = settings.embedding_api_key or settings.llm_api_key
        base_url = settings.embedding_base_url or settings.llm_base_url

        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            check_embedding_ctx_length=False,  # Skip context length check
            dimensions=None,  # Don't specify dimensions, let model decide automatically
        )

    def chat(self, messages: List[dict], system_prompt: Optional[str] = None) -> str:
        """
        Send conversation request and get response
        
        Args:
            messages: Conversation history message list, each contains role and content
                     Format: [{"role": "user", "content": "Hello"}, ...]
            system_prompt: System prompt (optional), used to set AI's role and behavior
        
        Returns:
            AI response text content
        """
        # Convert dictionary format messages to LangChain message objects
        langchain_messages = self._convert_messages(messages, system_prompt)

        try:
            # Call LLM to get response
            response = self.llm.invoke(langchain_messages)
            return response.content
        except Exception as e:
            # Error handling: return friendly error message
            print(f"[LLM Call Error] {str(e)}")
            return f"Sorry, AI service is temporarily unavailable, please try again later.\nError message: {str(e)}"

    def _convert_messages(self, messages: List[dict], system_prompt: Optional[str] = None) -> List[BaseMessage]:
        """
        Convert dictionary format messages to LangChain message objects
        
        LangChain uses specific message classes to distinguish messages from different roles:
        - SystemMessage: System prompt
        - HumanMessage: User messages
        - AIMessage: AI response messages
        
        Why convert?
        Unified message format allows LangChain to easily handle format differences between various LLMs internally.
        """
        result = []

        # First add system prompt (if any)
        if system_prompt:
            result.append(SystemMessage(content=system_prompt))

        # Convert history messages
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            elif role == "system":
                result.append(SystemMessage(content=content))
            # Ignore other roles or treat as user messages

        return result

    def get_embedding(self, text: str) -> List[float]:
        """
        Get vector representation of text (embedding)
        
        Args:
            text: Input text
        
        Returns:
            Vector list (float array)
        """
        return self.embedding_model.embed_query(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Batch get vector representations of texts
        
        Args:
            texts: Input text list
        
        Returns:
            List of vector lists
        """
        return self.embedding_model.embed_documents(texts)

    def get_llm_instance(self, temperature: float = None):
        """
        Get underlying LLM instance (for LangChain Agent and other advanced features)
        
        Args:
            temperature: Temperature parameter, if not provided uses default configuration
                        Agent tasks recommend 0.1-0.3, conversation tasks recommend 0.7
        """
        if temperature is None:
            return self.llm
        
        # Create LLM instance with custom temperature
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=temperature,
            max_tokens=2048,
        )

    def get_embedding_instance(self):
        """Get underlying embedding model instance (for Chroma and other vector databases)"""
        return self.embedding_model


# Global singleton instance
# Why use singleton? LLM instance creation cost is low, but unified management is more convenient,
# and avoids repeated connection creation overhead
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get LLM service singleton
    
    Global unified entry point, ensures the entire application uses the same LLM service instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service