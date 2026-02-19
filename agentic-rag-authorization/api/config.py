"""API configuration."""

from typing import List
from pydantic import BaseModel


class APIConfig(BaseModel):
    """API configuration settings."""

    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    api_prefix: str = "/api"


def get_api_config() -> APIConfig:
    """Get API configuration."""
    return APIConfig()
