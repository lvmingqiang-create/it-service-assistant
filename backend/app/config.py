"""
Configuration Management Module
================================
Responsible for统一管理 all project configuration items, read from environment variables, easy to switch environments during deployment.

Design:
- Uses pydantic-settings' BaseSettings to automatically load configuration from environment variables and .env files
- All sensitive information (API Keys, etc.) injected via environment variables, not hardcoded in code
- Supports switching between multiple LLM providers, defaults to OpenAI compatible interface
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application Configuration Class
    
    All configuration items can be overridden via environment variables, environment variable names match attribute names (uppercase).
    Example: Setting LLM_PROVIDER=openai will override the default value of llm_provider.
    """

    # ========== Basic Configuration ==========
    # Application name
    app_name: str = "Enterprise IT Service Smart Assistant"
    # Runtime environment: development / production
    environment: str = "development"
    # Service port
    port: int = 8000

    # ========== LLM Configuration (Multi-Provider Architecture) ==========
    # LLM provider: openai_compatible (OpenAI compatible interface, supports Volcengine/Doubao/Tongyi, etc.)
    llm_provider: str = "openai_compatible"
    
    # API Key (read from environment variable, do NOT write in code!)
    # Example: Volcengine/Doubao/Tongyi Qianwen and other platforms all provide OpenAI compatible API Keys
    llm_api_key: str = "sk-your-api-key-here"
    
    # API Base URL (required in compatible mode)
    # Volcengine: https://ark.cn-beijing.volces.com/api/v3
    # Doubao: https://ark.cn-beijing.volces.com/api/v3 (Doubao on Volcengine)
    # Tongyi Qianwen: https://dashscope.aliyuncs.com/compatible-mode/v1
    # DeepSeek: https://api.deepseek.com/v1
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    # Default model name
    # Volcengine example: doubao-pro-32k-241028 (need to create inference access point in console to obtain)
    # Tongyi Qianwen example: qwen-plus
    # DeepSeek example: deepseek-chat
    llm_model: str = "doubao-pro-32k-241028"
    
    # Embedding model name (used for RAG vectorization)
    # Volcengine example: doubao-embedding-240715
    # Tongyi Qianwen example: text-embedding-v2
    embedding_model: str = "doubao-embedding-240715"
    
    # Embedding model API Base URL (usually same as LLM)
    embedding_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    # Embedding model API Key (usually same as LLM)
    embedding_api_key: Optional[str] = None

    # ========== Vector Database Configuration ==========
    # Chroma data storage path (local file storage, no extra deployment needed)
    chroma_persist_directory: str = "./data/chroma"
    # Vector collection name
    chroma_collection_name: str = "it_knowledge_base"

    # ========== Document Processing Configuration ==========
    # Upload file save directory
    upload_dir: str = "./uploads"
    # Allowed file types
    allowed_file_types: list = ["pdf", "txt", "md"]
    # Document chunk size (characters)
    chunk_size: int = 500
    # Chunk overlap size (characters), maintains context continuity
    chunk_overlap: int = 50

    # ========== RAG Configuration ==========
    # Number of relevant documents to return during retrieval
    rag_top_k: int = 3

    # ========== CORS Configuration ==========
    # Allowed frontend origins (allows all in development environment)
    cors_origins: list = ["*"]

    class Config:
        """Pydantic Configuration: specifies .env file location"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance, import and use directly in project
settings = Settings()