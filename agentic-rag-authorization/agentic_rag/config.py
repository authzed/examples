"""Configuration management for agentic RAG system."""

from dataclasses import dataclass
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration for agentic RAG system."""

    # Milvus
    milvus_uri: str
    milvus_token: str

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
            milvus_uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
            milvus_token=os.getenv("MILVUS_TOKEN", ""),
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
