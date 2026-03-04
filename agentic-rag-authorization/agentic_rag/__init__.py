"""Agentic RAG with fine-grained authorization using Weaviate and SpiceDB."""

__version__ = "0.1.0"

# Initialize structured logging on module import
from .logging_config import setup_logging
from .config import get_config

setup_logging(level=get_config().log_level)
