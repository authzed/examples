"""Configuration management for agentic RAG system."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration for agentic RAG system."""

    # Weaviate
    weaviate_url: str
    weaviate_api_key: Optional[str]

    # SpiceDB
    spicedb_endpoint: str
    spicedb_token: str

    # OpenAI
    openai_api_key: str

    # Agent behavior
    max_retrieval_attempts: int = 1

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            weaviate_url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            weaviate_api_key=os.getenv("WEAVIATE_API_KEY"),
            spicedb_endpoint=os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
            spicedb_token=os.getenv("SPICEDB_TOKEN", "devtoken"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            max_retrieval_attempts=int(os.getenv("MAX_RETRIEVAL_ATTEMPTS", "1")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config.from_env()
