"""Shared helper functions for nodes."""

import time
from contextlib import contextmanager
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from .config import get_config


def get_llm() -> ChatOpenAI:
    """Get configured LLM instance.

    Returns:
        ChatOpenAI: Configured LLM with gpt-4 and temperature=0
    """
    config = get_config()
    return ChatOpenAI(
        model="gpt-4",
        temperature=0,
        api_key=config.openai_api_key
    )


@contextmanager
def log_node_execution(logger, node_name: str, extra: Dict[str, Any]):
    """Context manager for timing and logging node execution.

    Args:
        logger: Logger instance to use
        node_name: Name of the node being executed
        extra: Extra fields to include in log messages

    Yields:
        None

    Example:
        with log_node_execution(logger, "retrieval", {"query": query}):
            # ... node logic ...
            pass
    """
    start_time = time.time()
    logger.info(f"Starting {node_name}", extra=extra)

    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{node_name} complete",
            extra={**extra, "duration_ms": duration_ms}
        )
