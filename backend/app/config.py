from typing import List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multi-Agent Enterprise Code Reviewer & PR Quality Gate"
    VERSION: str = "1.0.0"

    # LLM Settings
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_REQUEST_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2

    # Qdrant & Embedding Settings
    QDRANT_MODE: str = "embedded"  # "embedded", "server", "auto"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "codebase_context"
    EMBEDDING_PROVIDER: str = "local"  # "local" or "openai"
    EMBEDDING_MODEL: str = "deterministic-384"
    EMBEDDING_DIM: int = 384

    # GitHub Integration Settings
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_DRY_RUN: bool = True

    # Quality Gate Defaults
    GATE_BLOCK_ON_CRITICAL: bool = True
    GATE_BLOCK_ON_HIGH: bool = True
    GATE_MAX_MEDIUM: int = 5
    GATE_MAX_LOW: int = 15

    # Storage & Workspace
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
    DB_PATH: str = os.path.join(os.path.dirname(__file__), "data", "reviews.db")
    MAX_CODE_SIZE_BYTES: int = 250_000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]


settings = Settings()
